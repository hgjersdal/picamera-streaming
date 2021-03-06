import io
import picamera
import logging
import socketserver
import threading
from http import server
import time

# Based on https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming

PAGE = """\
<html>
<head>
<title>click for picture</title>
</head>
<body style="background-color:#111111;">
<a href=picture>
<img src="stream.mjpg" title="Click to capture image"  height="100%" />
</a>
</body>
</html>
"""

PIC_PAGE = """\
<html>
<head>
<title>Click for stream</title>
</head>
<body style="background-color:#111111;">
<a href=index.html>
<img src="img.jpg" title="Click to watch stream" height=100% />
</a>
</body>
</html>
"""

take_picture = False  # Set to true to take a picture from camera thread
keep_looping = True  # Set to false to kill camera thread
mutex = threading.Lock()
counter = -1  # Count the number of stored images
request_power = False  # Does the camera need power?
timeout = 600  # Time in seconds until camera turns off after last request for power


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = threading.Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global take_picture
        global counter
        global request_power
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            mutex.acquire()
            request_power = True
            mutex.release()
            while(request_power):
                pass
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/picture':
            mutex.acquire()
            take_picture = True
            mutex.release()
            while(take_picture):
                pass
            content = PIC_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/img.jpg':
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.end_headers()
            with open('/home/pi/shared/img' + str(counter) + '.jpg', 'rb') as content:
                self.wfile.write(content.read())
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def check_input_thread(camera, output):
    """
    Thread function that takes captures frames if needed
    """
    global take_picture
    global counter
    global request_power
    global timeout
    cam_running = False
    t0 = 0
    while(keep_looping):
        time.sleep(0.01)
        mutex.acquire()
        if(request_power and not cam_running):
            t0 = time.time()
            if(not cam_running):
                camera.start_recording(output, format='mjpeg')
                cam_running = True
            request_power = False
        if(cam_running and time.time() - t0 > timeout):
            camera.stop_recording()
            cam_running = False
        if(take_picture):
            print("taking picture!")
            camera.stop_recording()
            resolution = camera.resolution
            camera.resolution = (4056, 3040)
            counter += 1
            camera.capture('/home/pi/shared/img' + str(counter) + '.jpg')
            camera.resolution = resolution
            take_picture = False
            camera.start_recording(output, format='mjpeg')
        mutex.release()
    if cam_running:
        camera.stop_recording()


with picamera.PiCamera(resolution='1296x972', framerate=24) as camera:
    output = StreamingOutput()
    camera.rotation = 90
    threading.Thread(target=check_input_thread, args=(camera, output), name='check_input', daemon=True).start()
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        print("going up!")
        while(True):
            server.serve_forever()
    finally:
        print("going down!")
        keep_looping = False

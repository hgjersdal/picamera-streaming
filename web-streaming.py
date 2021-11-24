import io
import picamera
import logging
import socketserver
import threading
from http import server

# Based on https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming


PAGE = """\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<img src="stream.mjpg" width="1296" height="972" /><br>
<input type=button onClick="location.href='picture'"
 value='Capture image'><br>
</body>
</html>
"""

PIC_PAGE = """\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<img src="stream.mjpg" width="1296" height="972" /><br>
<input type=button onClick="location.href='picture'"
 value='Capture image'><br>
<img src="img.jpg" width="4056" height="3040" />
</body>
</html>
"""

take_picture = False  # Set to true to take a picture from camera thread
keep_looping = True  # Set to false to kill camera thread
mutex = threading.Lock()
counter = -1  # Count the number of stored images


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
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
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
    while(keep_looping):
        mutex.acquire()
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


with picamera.PiCamera(resolution='1296x972', framerate=24) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
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
        camera.stop_recording()

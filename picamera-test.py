import picamera
import threading
import keyboard

keep_looping = True
camera = picamera.PiCamera()


def check_input_thread():
    global keep_looping
    global camera
    counter = 0
    resolution = camera.resolution
    zoom = camera.zoom
    while(True):
        key = keyboard.read_key()
        if(key == 'p'):
            camera.resolution = (4056, 3040)
            camera.capture('/home/pi/shared/img' + str(counter) + '.jpg')
            counter += 1
            camera.resolution = resolution
        elif(key == 'z'):
            if resolution == camera.resolution:
                camera.resolution = (4056, 3040)
                camera.zoom = (0.33, 0.33, 0.33, 0.33)
            else:
                camera.resolution = resolution
                camera.zoom = zoom
        elif(key == 'q'):
            keep_looping = False
            break


def preview():
    camera.start_preview()
    print(camera.resolution)
    print(camera.zoom)
    threading.Thread(target=check_input_thread, args=(), name='check_input', daemon=True).start()
    while(keep_looping):
        pass

    print(camera.resolution)
    camera.stop_preview()


preview()

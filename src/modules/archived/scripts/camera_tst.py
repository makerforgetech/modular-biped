import time
import picamera

with picamera.PiCamera() as camera:
        camera.start_preview()
        print('preview started')
        time.sleep(10)
        camera.stop_preview()
        print('preview ended')

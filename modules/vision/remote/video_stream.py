import cv2
from threading import Thread
from pubsub import pub

class VideoStream:
    def __init__(self, remote_source, **kwargs):
        self.remote_source = remote_source
        self.stream = cv2.VideoCapture(self.remote_source)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        pub.subscribe(self.stop, 'exit')
        
    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                self.stream.release()
                return
            self.grabbed, self.frame = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True

import cv2
from threading import Thread
from pubsub import pub

# Define VideoStream class to handle streaming of video from webcam in separate processing thread
# Source - Adrian Rosebrock, PyImageSearch: https://www.pyimagesearch.com/2015/12/28/increasing-raspberry-pi-fps-with-python-and-opencv/
class VideoStream:
    """Camera object that controls video streaming from the Picamera"""

    def __init__(self, index=0, resolution=(640, 480), framerate=30):
        # Initialize the PiCamera and the camera image stream
        self.stream = None
        self.configure(resolution, index)

        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

        # Variable to control when the camera is stopped
        self.stopped = False
        pub.subscribe(self.stop, 'exit')

    def start(self):
        # Start the thread that reads frames from the video stream
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def configure(self, res, index=0):
        if self.stream is not None:
            self.stream.release()
        self.stream = cv2.VideoCapture(index)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.set_resolution(res)
        return self.stream

    def set_resolution(self, res):
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, res[0])
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, res[1])

    def read(self):
        # Return the most recent frame
        return self.frame

    def stop(self):
        # Indicate that the camera and thread should be stopped
        self.stopped = True

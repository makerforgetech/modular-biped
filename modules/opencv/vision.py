from datetime import datetime, timedelta
import cv2
from imutils.video import FPS # for FSP only

try:
    from modules.opencv.faces import Faces
except ModuleNotFoundError as e:
    # Local execution
    from faces import Faces
    import os
    from video_stream import VideoStream
    

from pubsub import pub

class Vision:
    MODE_MOTION = 0
    MODE_FACES = 1

    def __init__(self, video, **kwargs):
        self.mode = kwargs.get('mode', Vision.MODE_MOTION)
        self.path = kwargs.get('path', '/')
        self.index = kwargs.get('index', 0)
        self.static_back = None
        self.dimensions = kwargs.get('resolution', (640, 480))
        self.preview = kwargs.get('preview', False)
        self.accuracy = kwargs.get('accuracy', 10) # Was 5

        self.flip = kwargs.get('flip', False)
        self.rotate = kwargs.get('rotate', False)
        self.video = video
        self.lines = []
        self.current_match = False
        self.last_match = datetime.now()  # @todo improve
        pub.subscribe(self.exit, "exit")

        # start the FPS counter
        self.fps = FPS().start()

        if self.mode == Vision.MODE_FACES:
            self.cascade_path = self.path + "/haarcascade_frontalface_default.xml"
            self.cascade = cv2.CascadeClassifier(self.cascade_path)
            self.faces = Faces(detector=self.cascade, path=self.path)

        self.running = True

    def exit(self):
        self.running = False
        self.video.stop()
        # Destroying all the windows
        cv2.destroyAllWindows()
        self.fps.stop()
        pub.sendMessage("log", msg="[Vision] Approx. FPS: {:.2f}".format(self.fps.fps()))
        
    def reset(self):
        self.static_back = None

    def detect(self):
        if not self.running:
            return
        # if not self.video.stream.isOpened():
        #     raise Exception('Unable to load camera')
        # update the FPS counter
        self.fps.update()

        matches = []

        frame = self.video.read()
        if frame is None:
            return

        if self.flip is True:
            frame = cv2.flip(frame, 0)

        if self.rotate is True:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # face detection
        if self.mode == Vision.MODE_FACES:
            # frame = cv2.flip(frame, 0)
            matches = self.cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=self.accuracy,
                minSize=(30, 30)
            )
            if len(matches) < 1:
                if self.current_match:
                    self.current_match = False
                    pub.sendMessage('vision:nomatch')
                if self.preview is False:
                    return matches

            names = []
            cnt = 0
            for (x, y, w, h) in matches:
                cropped = frame[y:y+h,x:x+w]
                cnt = cnt + 1
                names = names + self.faces.detect(cropped, [(0, 0, w, h)], cnt == len(matches))
        # motion
        elif self.mode == Vision.MODE_MOTION:
            #check, frame = self.video.read()
            # frame = cv2.flip(frame, -1)

            # Converting color image to gray_scale image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Converting gray scale image to GaussianBlur
            # so that change can be find easily
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # In first iteration we assign the value
            # of static_back to our first frame
            if self.static_back is None:
                self.static_back = gray
                return

            # Difference between static background
            # and current frame(which is GaussianBlur)
            diff_frame = cv2.absdiff(self.static_back, gray)

            # If change in between static background and
            # current frame is greater than 30 it will show white color(255)
            thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
            thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

            # Finding contour of moving object
            (_, cnts, _) = cv2.findContours(thresh_frame.copy(),
                                            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in cnts:
                if cv2.contourArea(contour) < 10000:
                    continue

                (x, y, w, h) = cv2.boundingRect(contour)
                matches.append((x, y, w, h))

        if self.preview:
            self.render(frame, matches, names)

        if len(matches) > 0:
            self.current_match = True
            self.last_match = datetime.now()

        return matches

        # key = cv2.waitKey(1)
        # # if q entered whole process will stop
        # if key == ord('q'):
        #     break

    def render(self, frame, matches, names):
        index = 0
        for (x, y, w, h) in matches:
            #making green rectangle around the moving object
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            if names is not None and names[index] is not None:
                y = y - 15 if y - 15 > 15 else y + 15
                cv2.putText(frame, names[index], (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                        .8, (0, 255, 255), 2)
            index = index + 1

        if self.lines:
            for (start, end) in self.lines:
                cv2.line(frame, start, end, (255, 0, 0), 2)

        # Displaying color frame with contour of motion of object
        cv2.imshow("Preview", frame)
        cv2.waitKey(1)

    def add_lines(self, lines):
        """
        Add lines to draw on screen in next render operation
        :param lines: [(x, y)]
        """
        self.lines = self.lines + list(set(lines) - set(self.lines))

    def get_area(self, match):
        """
        Wrapper to return area calculation.
        Deliberately not a static method so that it can be accessed via dependency injection
        :param match: cv2 match
        :return: area calcualation
        """
        if match is not None:
            x, y, w, h = match
            return float(w) * float(h)
        return 0


if __name__ == '__main__':
    path = os.path.dirname(__file__)
    camera_resolution = (640, 480) #(1024, 768) #- this halves the speed of image recognition
    video_stream = VideoStream(resolution=camera_resolution).start()
    vision = Vision(video_stream, mode=Vision.MODE_FACES, path=path, preview=True, resolution=camera_resolution)
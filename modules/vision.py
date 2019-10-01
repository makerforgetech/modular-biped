import cv2


class Vision:
    MODE_MOTION = 0
    MODE_FACES = 1

    def __init__(self, **kwargs):
        self.mode = kwargs.get('mode', Vision.MODE_MOTION)
        self.index = kwargs.get('index', 0)
        self.video = cv2.VideoCapture(self.index)
        self.static_back = None
        self.preview = kwargs.get('preview', False)
        self.dimensions = (640, 480)
        self.flip = kwargs.get('flip', True)
        self.lines = []

        if self.mode == Vision.MODE_FACES:
            self.cascade_path = "/home/pi/really-useful-robot/haarcascade_frontalface_default.xml"
            self.cascade = cv2.CascadeClassifier(self.cascade_path)

    def __del__(self):
        self.video.release()
        # Destroying all the windows
        cv2.destroyAllWindows()

    def detect(self):
        if not self.video.isOpened():
            raise Exception('Unable to load camera')

        matches = []

        check, frame = self.video.read()
        if self.flip:
            frame = cv2.flip(frame, 0)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # face detection
        if self.mode == Vision.MODE_FACES:
            # frame = cv2.flip(frame, 0)
            matches = self.cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
        # motion
        elif self.mode == Vision.MODE_MOTION:
            check, frame = self.video.read()
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
            self.render(frame, matches)

        return matches

        # key = cv2.waitKey(1)
        # # if q entered whole process will stop
        # if key == ord('q'):
        #     break

    def render(self, frame, matches):
        for (x, y, w, h) in matches:
            # making green rectangle around the moving object
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

        if self.lines:
            for key in self.lines:
                cv2.line(frame, self.lines[key][0], self.lines[key][1], (255, 0, 0), 2)

        # Displaying color frame with contour of motion of object
        cv2.imshow("Preview", frame)
        cv2.waitKey(25)

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
        return cv2.contourArea(match)

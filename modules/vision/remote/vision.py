import cv2
from datetime import datetime
from imutils.video import FPS
from pubsub import pub

try:
    from modules.vision.remote.faces import Faces
except ModuleNotFoundError as e:
    from faces import Faces
from modules.vision.remote.video_stream import VideoStream

class RemoteVision:
    MODE_MOTION = 0
    MODE_FACES = 1

    def __init__(self, **kwargs):
        self.remote_source = kwargs.get('remote_source', 'http://robot_ip:port/video')
        self.video = VideoStream(self.remote_source, **kwargs).start()
        self.mode = kwargs.get('mode', RemoteVision.MODE_MOTION)
        self.path = kwargs.get('path', '/')
        self.flip = kwargs.get('flip', False)
        self.rotate = kwargs.get('rotate', False)
        self.preview = kwargs.get('preview', False)
        self.accuracy = kwargs.get('accuracy', 10)
        self.static_back = None
        self.fps = FPS().start()
        pub.subscribe(self.exit, "exit")
        
        if self.mode == RemoteVision.MODE_FACES:
            self.cascade_path = self.path + "/modules/vision/haarcascade_frontalface_default.xml"
            self.cascade = cv2.CascadeClassifier(self.cascade_path)
            self.faces = Faces(detector=self.cascade, path=self.path)
        
        self.running = True

    def exit(self):
        self.running = False
        if self.video and hasattr(self.video, "stop"):
            self.video.stop()
        cv2.destroyAllWindows()
        self.fps.stop()
        pub.sendMessage("log", msg="[RemoteVision] Approx. FPS: {:.2f}".format(self.fps.fps()))

    def detect(self):
        if not self.running:
            return
        self.fps.update()
        frame = self.video.read()
        if frame is None:
            return

        if self.flip:
            frame = cv2.flip(frame, 0)
        if self.rotate:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        matches = []
        names = []
        
        if self.mode == RemoteVision.MODE_FACES:
            matches = self.cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=self.accuracy,
                minSize=(30, 30)
            )
            if len(matches) > 0:
                cnt = 0
                for (x, y, w, h) in matches:
                    cropped = frame[y:y+h, x:x+w]
                    cnt += 1
                    names += self.faces.detect(cropped, [(0, 0, w, h)], cnt == len(matches))
        elif self.mode == RemoteVision.MODE_MOTION:
            gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)
            if self.static_back is None:
                self.static_back = gray_blur
                return
            diff_frame = cv2.absdiff(self.static_back, gray_blur)
            thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1]
            thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)
            contours, _ = cv2.findContours(thresh_frame.copy(),
                                           cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                if cv2.contourArea(contour) < 10000:
                    continue
                (x, y, w, h) = cv2.boundingRect(contour)
                matches.append((x, y, w, h))
                
        if self.preview:
            self.render(frame, matches, names)
        return matches

    def render(self, frame, matches, names):
        index = 0
        for (x, y, w, h) in matches:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            if names and index < len(names):
                label_y = y - 15 if y - 15 > 15 else y + 15
                cv2.putText(frame, names[index], (x, label_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            index += 1
        cv2.imshow("Remote Preview", frame)
        cv2.waitKey(1)

    def get_area(self, match):
        if match is not None:
            x, y, w, h = match
            return float(w) * float(h)
        return 0

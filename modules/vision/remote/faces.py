import face_recognition
import pickle
import cv2
import time
from collections import Counter
import shutil
from pubsub import pub

class Faces:
    UNKNOWN_LABEL = 'Unknown'
    MATCH_THRESHOLD_PERCENT = 40

    def __init__(self, **kwargs):
        self.path = kwargs.get('path', '/')
        encodingsP = self.path + "/encodings.pickle"
        cascade = self.path + "/haarcascade_frontalface_default.xml"
        self.last_face = None
        self.last_save = None
        self.data = pickle.loads(open(encodingsP, "rb").read())
        self.faceCounts = Counter(self.data['names'])
        self.detector = kwargs.get('detector', cv2.CascadeClassifier(cascade))
        pub.subscribe(self.nomatch, 'vision:nomatch')

    def nomatch(self):
        self.last_face = None

    def detect(self, rgb, matches, final_match):
        if rgb is None or matches is None:
            raise Exception('Inputs not found')
        boxes = [(y, x + w, y + h, x) for (x, y, w, h) in matches]
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []
        for encoding in encodings:
            matched_faces = face_recognition.compare_faces(self.data["encodings"], encoding)
            name = Faces.UNKNOWN_LABEL
            if True in matched_faces:
                matchedIdxs = [i for (i, b) in enumerate(matched_faces) if b]
                counts = {}
                for i in matchedIdxs:
                    nm = self.data["names"][i]
                    counts[nm] = counts.get(nm, 0) + 1
                biggestHit = max(counts, key=counts.get)
                if counts[biggestHit] > (self.faceCounts[biggestHit] / 100 * Faces.MATCH_THRESHOLD_PERCENT):
                    name = biggestHit
            if self.last_face != name:
                self.last_face = name
            pub.sendMessage('vision:detect:face', name=name)
            names.append(name)
        # Save images periodically (if space permits)
        if self.last_save is None or self.last_save < time.time() - 5:
            if final_match:
                self.last_save = time.time()
            for name in names:
                cv2.imwrite(self.path + '/matches/' + name + '/' + str(time.time() * 1000) + '.jpg', rgb)
        return names

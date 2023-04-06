# import the necessary packages
import face_recognition
import pickle
import cv2
import time
from collections import Counter
import shutil
from pubsub import pub

class Faces:
    MODE_MOTION = 0
    MODE_FACES = 1

    MATCH_THRESHOLD_PERCENT = 40
    UNKNOWN_LABEL = 'Unknown'

    def __init__(self, **kwargs):
        self.path = kwargs.get('path', '/')
        # Determine faces from encodings.pickle file model created from train_model.py
        encodingsP = self.path + "/encodings.pickle"
        # use this xml file
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


        # OpenCV returns bounding box coordinates in (x, y, w, h) order
        # but we need them in (top, right, bottom, left) order, so we
        # need to do a bit of reordering
        boxes = [(y, x + w, y + h, x) for (x, y, w, h) in matches]

        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []

        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matched_faces = face_recognition.compare_faces(self.data["encodings"],
                                                     encoding)
            name = Faces.UNKNOWN_LABEL  # if face is not recognized, then print Unknown

            # check to see if we have found a match
            if True in matched_faces:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matched_faces) if b]
                counts = {}

                # loop over the matched indexes and maintain a count for each recognized face
                # returns the number of matches against each name (e.g. {'Dan': 44, 'Lily': 1})
                for i in matchedIdxs:
                    nm = self.data["names"][i]
                    counts[nm] = counts.get(nm, 0) + 1

                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                biggestHit = max(counts, key=counts.get)
                # print(biggestHit + ': ' + str(counts[biggestHit]) + '(min: ' + str(self.faceCounts[biggestHit] / 100 * Faces.MATCH_THRESHOLD_PERCENT) + ')')
                if counts[biggestHit] > (self.faceCounts[biggestHit] /100 * Faces.MATCH_THRESHOLD_PERCENT):
                    # print('MATCH: ' + biggestHit)
                    name = biggestHit

            if self.last_face != name:
                self.last_face = name

            pub.sendMessage('vision:detect:face', name=name)

            # update the list of names
            names.append(name)


        space = True
        ## Check disk space every 500 seconds to ensure we're not filling the drive
        if self.last_save is None or self.last_save < time.time() - 500:
            total, used, free = shutil.disk_usage("/")
            if (free // (2 ** 30)) < 2:
                print("NO SPACE!")
                space = False

        # Assuming there is space, save the camera frame to the match's folder
        if space and self.last_save is None or self.last_save < time.time() - 5:
            if final_match:
                self.last_save = time.time()
            for name in names:
                #print("SAVING to " + name)
                # Periodically save frames for match improvements
                cv2.imwrite(self.path + '/matches/' + name + '/' + str(time.time() * 1000) + '.jpg', rgb)

        return names
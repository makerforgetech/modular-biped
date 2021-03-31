# import the necessary packages
import face_recognition
import pickle
import cv2


class Faces:
    MODE_MOTION = 0
    MODE_FACES = 1

    def __init__(self, **kwargs):

        # Initialize 'currentname' to trigger only when a new person is identified.
        self.unknown_label = "Unknown"
        # Determine faces from encodings.pickle file model created from train_model.py
        encodingsP = "/home/pi/really-useful-robot/encodings.pickle"
        # use this xml file
        cascade = "/home/pi/really-useful-robot/haarcascade_frontalface_default.xml"
        self.last_face = None

        self.data = pickle.loads(open(encodingsP, "rb").read())
        self.detector = kwargs.get('detector', cv2.CascadeClassifier(cascade))

    def detect(self, rgb, matches):
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
            name = self.unknown_label  # if face is not recognized, then print Unknown

            # check to see if we have found a match
            if True in matched_faces:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matched_faces) if b]
                counts = {}

                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = self.data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)

                # If someone in your dataset is identified, print their name on the screen
                if self.last_face != name:
                    self.last_face = name
                    print(self.last_face)

            # update the list of names
            names.append(name)

        return names
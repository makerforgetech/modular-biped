from imutils import paths
import face_recognition
import pickle
import cv2
import os
import shutil
from pubsub import pub

class TrainModel:
    def __init__(self, **kwargs):
        self.path = kwargs.get('dataset', 'dataset')
        self.output = kwargs.get('output', 'encodings.pickle')
        pub.subscribe(self.train, 'vision:train')

    def train(self):
        # ...existing code...
        imagePaths = list(paths.list_images(self.path))
        if len(imagePaths) < 1:
            pub.sendMessage('log', msg='[TrainModel] Nothing to process')
            return
        pub.sendMessage('log', msg='[TrainModel] Start processing faces...')
        knownEncodings = []
        knownNames = []
        for (i, imagePath) in enumerate(imagePaths):
            if '.AppleDouble' in imagePath:
                continue
            pub.sendMessage('log', msg='[TrainModel] processing image {}/{} - {}'.format(i + 1, len(imagePaths), imagePath))
            name = imagePath.split(os.path.sep)[-2]
            image = cv2.imread(imagePath)
            if image is None:
                continue
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, boxes)
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(name)
        pub.sendMessage('log', msg='[TrainModel] serializing encodings...')
        data = {"encodings": knownEncodings, "names": knownNames}
        with open(self.output, "wb") as f:
            f.write(pickle.dumps(data))
        pub.sendMessage('log', msg='[TrainModel] Saved to ' + self.output)
        # Optionally, move dataset folder if needed:
        # trained_dir = os.path.abspath(os.path.join(self.path, os.pardir)) + '/trained'
        # shutil.move(self.path, trained_dir)
        # pub.sendMessage('log', msg='[TrainModel] Moved ' + self.path + ' to ' + trained_dir)

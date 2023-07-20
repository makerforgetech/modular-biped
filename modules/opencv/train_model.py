#! /usr/bin/python

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
		# our images are located in the dataset folder
		imagePaths = list(paths.list_images(self.path))

		if len(imagePaths) < 1:
			pub.sendMessage('log', msg='[TrainModel] Nothing to process')
			return

		pub.sendMessage('log', msg='[TrainModel] Start processing faces...')
		# initialize the list of known encodings and known names
		knownEncodings = []
		knownNames = []

		# loop over the image paths
		for (i, imagePath) in enumerate(imagePaths):
			if '.AppleDouble' in imagePath:
				continue
			# extract the person name from the image path
			pub.sendMessage('log', msg='[TrainModel] processing image {}/{} - {}'.format(i + 1, len(imagePaths), imagePath))
			name = imagePath.split(os.path.sep)[-2]

			# load the input image and convert it from RGB (OpenCV ordering)
			# to dlib ordering (RGB)
			image = cv2.imread(imagePath)
			if image is None:
				continue
			rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

			# detect the (x, y)-coordinates of the bounding boxes
			# corresponding to each face in the input image
			boxes = face_recognition.face_locations(rgb,
				model="hog")

			# compute the facial embedding for the face
			encodings = face_recognition.face_encodings(rgb, boxes)

			# loop over the encodings
			for encoding in encodings:
				# add each encoding + name to our set of known names and
				# encodings
				knownEncodings.append(encoding)
				knownNames.append(name)

		# dump the facial encodings + names to disk
		pub.sendMessage('log', msg='[TrainModel] serializing encodings...')
		# @todo add to existing encodings, then overwrite existing file
		data = {"encodings": knownEncodings, "names": knownNames}
		f = open(self.output, "wb")
		f.write(pickle.dumps(data))
		f.close()
		pub.sendMessage('log', msg='[TrainModel] Saved to ' + self.output)
		# trained_dir = os.path.abspath(os.path.join(self.path, os.pardir)) +'/trained'
		# shutil.move(self.path, trained_dir)
		# pub.sendMessage('log', msg='[TrainModel] Moved ' + self.path + ' to ' + trained_dir)
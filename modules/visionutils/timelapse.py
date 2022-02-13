# import the necessary packages
import cv2
import time
from pubsub import pub
# from utils import CFEVideoConf, image_resize
import glob, os

class Timelapse:
    SECONDS_BETWEEN_FRAMES = 1
    OUTPUT_FPS = 20

    def __init__(self, **kwargs):
        self.path = kwargs.get('path', '/')
        self.timelapse_folder = self.path + kwargs.get('folder', '/timelapse')
        self.output_path = self.path + kwargs.get('file', '/timelapse.mp4')
        self.dimensions = kwargs.get('dimensions', (640, 480))
        self.last_save = None

        self.running = False
        pub.subscribe(self.process, 'vision:image')
        pub.subscribe(self.start, 'vision:timelapse:start')
        pub.subscribe(self.stop, 'vision:timelapse:stop')

    def start(self):
        self.running = True
        self.last_save = time.time()

    def stop(self):
        self.running = False
        self.output(False)

    def process(self, image):
        if not self.running or image is None or self.last_save > time.time() - Timelapse.SECONDS_BETWEEN_FRAMES:
            return
        file = self.timelapse_folder + '/' + str(time.time() * 1000) + '.jpg'
        self.last_save = time.time()
        cv2.imwrite(file, image)

    def output(self, clear_images=True):
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        out = cv2.VideoWriter(self.output_path, fourcc, Timelapse.OUTPUT_FPS, self.dimensions)

        image_list = glob.glob(self.timelapse_folder + "/*.jpg")
        sorted_images = sorted(image_list, key=os.path.getmtime)
        for file in sorted_images:
            image_frame = cv2.imread(file)
            out.write(image_frame)
        if clear_images:
            '''
            Remove stored timelapse images
            '''
            for file in image_list:
                os.remove(file)

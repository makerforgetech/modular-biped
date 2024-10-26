# import the necessary packages
import cv2
import time
from pubsub import pub
from threading import Thread
# from utils import CFEVideoConf, image_resize
import glob, os

# for concatenating files
# from moviepy.editor import *
# from natsort import natsorted

class Timelapse:
    SECONDS_BETWEEN_FRAMES = 1
    SECONDS_BETWEEN_OUTPUTS = 60 # Used for mode where frames are stored in memory.
    OUTPUT_FPS = 20

    def __init__(self, video, **kwargs):
        self.path = kwargs.get('path', '/')
        self.timelapse_folder = self.path + kwargs.get('folder', '/timelapse')
        self.resolution = kwargs.get('resolution', (1024, 768))
        self.original_resolution = kwargs.get('original_resolution', (640, 480))
        self.last_save = None
        self.last_output = None

        self.video = video
        self.frames = []
        self.save_frames = False # Store frames in memory and output to video file periodically, or save each frame and output once stopped.

        self.running = False
        # pub.subscribe(self.process, 'vision:image')
        pub.subscribe(self.start, 'vision:timelapse:start')
        pub.subscribe(self.stop, 'vision:timelapse:stop')
        pub.subscribe(self.stop, 'exit')
        pub.subscribe(self.output, 'vision:timelapse:output')

    def start(self):
        if self.running:
            return
        pub.sendMessage('log', msg='[TIMELAPSE] Starting')
        pub.sendMessage('led:full', color='white')
        if self.resolution != self.original_resolution:
            self.video.set_resolution(self.resolution) # change image resolution here
        self.running = True
        self.last_save = time.time()
        self.last_output = time.time()
        Thread(target=self.process, args=()).start()

    def stop(self):
        if not self.running:
            return
        pub.sendMessage('log', msg='[TIMELAPSE] Stopping')
        self.running = False
        pub.sendMessage('led:full', color='off')
        if not self.save_frames:
            self.output_from_ram()
        if self.resolution != self.original_resolution:
            self.video.set_resolution(self.original_resolution)

    def process(self):
        pub.sendMessage('log', msg='[TIMELAPSE] Running...')
        while self.running:
            image = self.video.read()
            if image is None or self.last_save > time.time() - Timelapse.SECONDS_BETWEEN_FRAMES:
                continue

            self.last_save = time.time()
            if self.save_frames:
                file = self.timelapse_folder + '/' + str(time.time() * 1000) + '.jpg'
                cv2.imwrite(file, image)
            else:
                self.frames.append(image)
                if self.last_output < time.time() - Timelapse.SECONDS_BETWEEN_OUTPUTS:
                    self.output_from_ram()

            sleep_time = self.last_save - time.time() + Timelapse.SECONDS_BETWEEN_FRAMES
            if sleep_time > 0:
                time.sleep(sleep_time)

    def output_from_ram(self):
        pub.sendMessage('log', msg='[TIMELAPSE] Outputting from RAM ' + str(len(self.frames)) + ' frames - Start:' +  str(time.time()))
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        out = cv2.VideoWriter(self.path + '/timelapse/' + str(time.time() * 1000) + '.mp4', fourcc, Timelapse.OUTPUT_FPS, self.resolution)

        for file in self.frames:
            out.write(file)
        self.frames = []
        self.last_output = time.time()
        pub.sendMessage('log', msg='[TIMELAPSE] Outputting from RAM - End:' + str(time.time()))

    def output(self):
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        out = cv2.VideoWriter(self.path + '/timelapse/' + str(time.time() * 1000) + '.mp4', fourcc, Timelapse.OUTPUT_FPS, self.resolution)

        image_list = glob.glob(self.timelapse_folder + "/*.jpg")
        pub.sendMessage('log', msg='[TIMELAPSE] Outputting from files ' + str(len(image_list)) + ' frames - Start:' + str(time.time()))
        sorted_images = sorted(image_list, key=os.path.getmtime)
        for file in sorted_images:
            image_frame = cv2.imread(file)
            out.write(image_frame)
            # os.remove(file)
        pub.sendMessage('log', msg='[TIMELAPSE] Outputting from files - End:' + str(time.time()))

    # def concat_files(self):
    #     L = []
    #     for root, dirs, files in os.walk(self.path + '/timelapse'):
    #         # files.sort()
    #         files = natsorted(files)
    #         for file in files:
    #             if os.path.splitext(file)[1] == '.mp4':
    #                 filePath = os.path.join(root, file)
    #                 video = VideoFileClip(filePath)
    #                 L.append(video)
    #
    #     final_clip = concatenate_videoclips(L)
    #     final_clip.to_videofile(self.path + "/timelapse.mp4", fps=Timelapse.OUTPUT_FPS, remove_temp=False)
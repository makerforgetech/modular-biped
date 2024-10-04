from pubsub import pub

import asyncio
import os

import setenv # I added this

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.services.vision import VisionClient
from viam.components.camera import Camera
from datetime import datetime, timedelta
from viam.logging import getLogger
LOGGER = getLogger(__name__)
LOGGER.debug('INIT MAKERFORGE VIAMOBJECTS')

class ViamObjects:
    def __init__(self, robot, **kwargs):
        self.enabled = False
        pub.subscribe(self.enable, 'vision:start')
        pub.subscribe(self.exit, 'exit')
        self.robot = robot
        # make sure that your detector name in the app matches "myPeopleDetector"
        self.detector = VisionClient.from_robot(self.robot, "objectDetector")
        # make sure that your camera name in the app matches "my-camera"
        self.camera = Camera.from_robot(robot=self.robot, name="camera")
        self.last_capture = datetime.now() - timedelta(seconds=60)
        self.disable_timeout = None # Used to disable vision after 5 seconds of no detections

    def enable(self):
        # print("ENABLING VISION")
        pub.sendMessage("led", identifiers=['status5'], color='white_dim')
        self.disable_timeout = datetime.now() + timedelta(seconds=5)
        self.enabled = True
        
    def disable(self):
        # print("DISABLING VISION")
        pub.sendMessage("led", identifiers=['status5'], color='off')
        self.enabled = False
        
    def exit(self):
        pass
    
    async def detect(self):
        if not self.enabled:
            return
        if self.last_capture + timedelta(seconds=60) > datetime.now():
            return
        print("DETECTING ENABLED")
        pub.sendMessage("led:eye", color='white_dim')
        img = await self.camera.get_image()
        detections = await self.detector.get_detections(img)

        found = False
        date_time = datetime.now().strftime("%m%d%Y%H%M%S%f")
        for d in detections:
            if d.confidence > 0.6:
                pub.sendMessage('log', msg='Object detected: ' + d.class_name)
                pub.sendMessage('vision:detect:object', name=d.class_name)
                self.disable_timeout = datetime.now() + timedelta(seconds=5)
                self.last_capture = datetime.now()
                pos = str(d.x_min).zfill(3) + str(d.y_min).zfill(3) + str(d.x_max).zfill(3) + str(d.y_max).zfill(3)
                print(d.class_name + pos)
                
                directory = '/home/archie/modular-biped/data/' + d.class_name.lower()
                if not os.path.exists(directory):
                    os.makedirs(directory)
                img.save(directory + '/' + date_time + pos + '.png')
                found = True
        pub.sendMessage("led:eye", color='blue')
        if found:
            return
        else:
            if self.disable_timeout < datetime.now():
                pub.sendMessage('vision:nomatch')
                self.disable()
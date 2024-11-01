from pubsub import pub

import asyncio
import os

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.services.vision import VisionClient
from viam.components.camera import Camera
from datetime import datetime, timedelta
from viam.logging import getLogger
LOGGER = getLogger(__name__)

class ViamObjects:
    def __init__(self, **kwargs):
        """
        Viam Objects
        Allows detection of objects using the VIAM Vision service
        
        Install the VIAM SDK before using.
        pip install viam-sdk
        
        Subscribes to:
        - vision:start
        - exit
        
        Publishes:
        - log
        - vision:detections
        - vision:nomatch
        
        :param robot: RobotClient instance (set after creation)
        Example:
        objects = ViamObjects()
        objects.robot = robot
        objects.enable()
        results = objects.detect()
        """
        self.enabled = False
        pub.subscribe(self.enable, 'vision:start')
        pub.subscribe(self.exit, 'exit')
        self._robot = None
        self.vision_client = kwargs.get('vision_client', 'objectDetector')
        self.camera_name = kwargs.get('camera_name', 'camera')
        self.timelapse_location = kwargs.get('timelapse_location')
       
        self.last_capture = datetime.now() - timedelta(seconds=60)
        self.disable_timeout = None # Used to disable vision after 5 seconds of no detections
        
    # Robot setter and getter
    @property
    def robot(self):
        return self._robot
    
    @robot.setter
    def robot(self, value):
        self._robot = value
         # make sure that your detector name in the app matches "myPeopleDetector"
        self.detector = VisionClient.from_robot(self.robot, self.vision_client)
        # make sure that your camera name in the app matches "my-camera"
        self.camera = Camera.from_robot(robot=self.robot, name=self.camera_name)

    def enable(self):
        # print("ENABLING VISION")
        self.disable_timeout = datetime.now() + timedelta(seconds=5)
        self.enabled = True
        
    def disable(self):
        # print("DISABLING VISION")
        self.enabled = False
        
    def exit(self):
        pass
    
    async def detect(self):
        if not self.enabled:
            return
        if self.last_capture + timedelta(seconds=60) > datetime.now():
            return
        img = await self.camera.get_image()
        detections = await self.detector.get_detections(img)

        found = False
        date_time = datetime.now().strftime("%m%d%Y%H%M%S%f")
        pub.sendMessage('vision:detections', matches=detections)
        for d in detections:
            if d.confidence > 0.6:
                pub.sendMessage('log', msg='Object detected: ' + d.class_name)
                self.disable_timeout = datetime.now() + timedelta(seconds=5)
                self.last_capture = datetime.now()
                pos = str(d.x_min).zfill(3) + str(d.y_min).zfill(3) + str(d.x_max).zfill(3) + str(d.y_max).zfill(3)
                # print(d.class_name + pos)
                
                found = True
                if self.timelapse_location is None:
                    directory = self.timelapse_location
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    img.save(directory + '/' + date_time + pos + '.png')
                
        if found:
            return
        else:
            if self.disable_timeout < datetime.now():
                pub.sendMessage('vision:nomatch')
                self.disable()
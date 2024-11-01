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

class ViamClassifier:
    def __init__(self, **kwargs):
        """
        Viam Classifier
        Allows classification of objects using the VIAM Vision service
        
        Install the VIAM SDK before using.
        pip install viam-sdk
        
        Requires secrets to be set in the environment variables:
        - ROBOT_API_KEY
        - ROBOT_API_KEY_ID
        - ROBOT_ADDRESS
        See wiki for more information.
        
        Subscribes to:
        - vision:start
        - exit
        
        Publishes:
        - log
        - vision:detections
        - vision:nomatch
        
        :param robot: RobotClient instance (set after creation)
        Example:
        classifier = ViamClassifier()
        classifier.robot = robot
        classifier.enable()
        results = classifier.detect()
        """
        self.enabled = False
        pub.subscribe(self.enable, 'vision:start')
        pub.subscribe(self.exit, 'exit')
        self._robot = None
        self.classifier_name = kwargs.get('classifier_name', 'my-classifier')
        self.camera_name = kwargs.get('camera_name', 'camera')
        self.last_capture = datetime.now() - timedelta(seconds=60)
        self.disable_timeout = None # Used to disable vision after 5 seconds of no detections
    
    @property
    def robot(self):
        return self._robot
    
    @robot.setter
    def robot(self, value):
        self._robot = value
        self.classifier = VisionClient.from_robot(self._robot, self.classifier_name)
        self.camera = Camera.from_robot(robot=self._robot, name=self.camera_name)
        
    def enable(self):
        self.disable_timeout = datetime.now() + timedelta(seconds=5)
        self.enabled = True
        
    def disable(self):
        self.enabled = False
        
    def exit(self):
        pass
    
    async def detect(self):
        if not self.enabled:
            return
        if self.last_capture + timedelta(seconds=1) > datetime.now():
            return
        
        img = await self.camera.get_image()
        detections = await self.classifier.get_classifications(img, 1)

        found = False
        date_time = datetime.now().strftime("%m%d%Y%H%M%S%f")
        # print(detections)
        pub.sendMessage('vision:detections', matches=detections)
        for d in detections:
            if d.confidence > 0.6:
                pub.sendMessage('log', msg='[Gesture] Detected: ' + d.class_name)
                self.disable_timeout = datetime.now() + timedelta(seconds=5)
                self.last_capture = datetime.now()
                found = True
        if found:
            return
        pub.sendMessage('log', msg='[Gesture] None')
        if self.disable_timeout < datetime.now():
            pub.sendMessage('vision:nomatch')
            self.disable()
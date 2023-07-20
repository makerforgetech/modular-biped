# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Performs continuous object detection with the camera.

"""

from modules.coral.aiymakerkit import vision as coralvision
from modules.coral.aiymakerkit import utils
import modules.coral.models as models
from threading import Thread
from pubsub import pub

class Vision:
    def __init__(self, **kwargs):
        self.preview = kwargs.get('preview', False)
        
        self.set_mode(kwargs.get('mode', 'object')) # intial mode, will switch dynamically during use
        self.new_thread = Thread(target=self.vision_thread)        
        self.new_thread.start()
        pub.subscribe(self.exit, 'exit')
        
    def set_mode(self, mode):
        self.mode = mode
        if mode == 'object':
            self.detector = coralvision.Detector(models.OBJECT_DETECTION_MODEL)
            self.labels = utils.read_labels_from_metadata(models.OBJECT_DETECTION_MODEL)
            self.threshold = 0.4
        else:
            self.detector = coralvision.Detector(models.FACE_DETECTION_MODEL)
            self.labels = None
            self.threshold = 0.1

    def exit(self):
        self.new_thread.join()

    def vision_thread(self):
        for frame in coralvision.get_frames(display=self.preview):
            objects = self.detector.get_objects(frame, threshold=self.threshold)
            if self.preview:
                coralvision.draw_objects(frame, objects, self.labels)
            # print(objects)
            # [Object(id=0, score=0.984375, bbox=BBox(xmin=157, ymin=116, xmax=621, ymax=469))]
            # print(self.labels)
            # {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'n/a', 12: 'stop sign', 13: 'parking meter', 14: 'bench', 15: 'bird', 16: 'cat', 17: 'dog', 18: 'horse', 19: 'sheep', 20: 'cow', 21: 'elephant', 22: 'bear', 23: 'zebra', 24: 'giraffe', 25: 'n/a', 26: 'backpack', 27: 'umbrella', 28: 'n/a', 29: 'n/a', 30: 'handbag', 31: 'tie', 32: 'suitcase', 33: 'frisbee', 34: 'skis', 35: 'snowboard', 36: 'sports ball', 37: 'kite', 38: 'baseball bat', 39: 'baseball glove', 40: 'skateboard', 41: 'surfboard', 42: 'tennis racket', 43: 'bottle', 44: 'n/a', 45: 'wine glass', 46: 'cup', 47: 'fork', 48: 'knife', 49: 'spoon', 50: 'bowl', 51: 'banana', 52: 'apple', 53: 'sandwich', 54: 'orange', 55: 'broccoli', 56: 'carrot', 57: 'hot dog', 58: 'pizza', 59: 'donut', 60: 'cake', 61: 'chair', 62: 'couch', 63: 'potted plant', 64: 'bed', 65: 'n/a', 66: 'dining table', 67: 'n/a', 68: 'n/a', 69: 'toilet', 70: 'n/a', 71: 'tv', 72: 'laptop', 73: 'mouse', 74: 'remote', 75: 'keyboard', 76: 'cell phone', 77: 'microwave', 78: 'oven', 79: 'toaster', 80: 'sink', 81: 'refrigerator', 82: 'n/a', 83: 'book', 84: 'clock', 85: 'vase', 86: 'scissors', 87: 'teddy bear', 88: 'hair drier', 89: 'toothbrush'}
            if len(objects) > 0:
                if self.mode == 'object':
                    pub.sendMessage('vision:detect:object', name=self.labels[objects[0].id])
                else:
                    pub.sendMessage('vision:detect:face', name="unknown")
                pub.sendMessage('vision:matches', matches=objects, labels=self.labels)
                # if any detected objects contains 'person' then set_mode to 'face'
                if self.mode == 'object':
                    for object in objects:
                        if self.labels[object.id] == 'person':
                            self.set_mode('face')
                            break
            else:
                pub.sendMessage('vision:nomatch')
                # if no faces detected, go back to object detection
                if self.mode == 'face':
                    self.set_mode('object')
            





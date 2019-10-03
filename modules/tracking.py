import cv2
from time import sleep
from datetime import datetime

class Tracking:
    def __init__(self, vision, pan, tilt, bounds_percent=15):
        self.vision = vision
        self.pan = pan
        self.tilt = tilt
        # define bounds around screen
        self.bounds_percent = bounds_percent
        self.bounds = int(self.vision.dimensions[0] / (100 / bounds_percent))
        self.vision.add_lines(self._define_boundary_lines())
        self.ignore = 0
        self.last_match = datetime.now() # @todo improve

    def track_largest_match(self):
        """
        Move the pan and tilt servos an incremental amount to attempt to keep the largest match
        within the defined bounds on screen

        Incremental amount is the percentage of the screen defined as boundary
        """
        largest = self._largest(self.vision.detect())
        if largest is None:
            return False
        
        # Run through the buffer to ignore cached matches
        if self.ignore > 0:
            self.ignore = self.ignore -1
            return False
        
        (x, y, w, h) = largest
        moved = False
        if x < self.bounds:
            self.pan.move_relative(-self.bounds_percent)
            moved = True
        elif (x + w) > (self.vision.dimensions[0] - self.bounds):
            self.pan.move_relative(self.bounds_percent)
            moved = True
        if y < self.bounds:
            self.tilt.move_relative(self.bounds_percent)
            moved = True
        elif (y + h) > (self.vision.dimensions[1] - self.bounds):
            self.tilt.move_relative(-self.bounds_percent)
            moved = True
        
        if moved == True:        
            self.vision.reset()
            self.ignore = 5
        
        self.last_match = datetime.now()
        return True

    def _define_boundary_lines(self):
        right = self.vision.dimensions[0]
        top = self.vision.dimensions[1]
        lines = [
            ((self.bounds, 0), (self.bounds, top)),
            ((right - self.bounds, 0), (right - self.bounds, top)),
            ((0, self.bounds), (right, self.bounds)),
            ((0, top - self.bounds), (right, top - self.bounds))
        ]
        return lines

    def _largest(self, matches):
        """
        Detect the largest of each match from the vision software
        :param matches:
        :return: (x, y, w, h) match
        """
        largest = None
        if matches is not None:
            for match in matches:
                if largest is None or self.vision.get_area(match) > self.vision.get_area(largest):
                    largest = match
            return largest
        return None

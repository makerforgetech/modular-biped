import cv2


class Tracking:
    def __init__(self, vision, pan, tilt, bounds_percent=25):
        self.vision = vision
        self.pan = pan
        self.tilt = tilt
        # define bounds around screen
        self.bounds_percent = bounds_percent
        self.bounds = self.vision.dimensions[0] / (100 / bounds_percent)
        self.vision.add_lines(self._define_boundary_lines())

    def track_largest_match(self):
        """
        Move the pan and tilt servos an incremental amount to attempt to keep the largest match
        within the defined bounds on screen

        Incremental amount is the percentage of the screen defined as boundary
        """
        largest = self._largest(self.vision.detect())
        if largest is None:
            return
        (x, y, w, h) = largest
        if x < self.bounds:
            self.pan.move_relative(self.bounds_percent)
        elif (x + w) > (self.vision.dimensions[0] - self.bounds):
            self.pan.move_relative(-self.bounds_percent)
        if y < self.bounds:
            self.tilt.move_relative(self.bounds_percent)
        elif (y + h) > (self.vision.dimensions[1] - self.bounds):
            self.tilt.move_relative(-self.bounds_percent)

    def _define_boundary_lines(self):
        right = self.vision.dimensions[0]
        top = self.vision.dimensions[1]
        lines = [
            ((self.bounds, 0), (self.bounds, top)),
            ((right - self.bounds, 0), (right - self.bounds, top)),
            ((0, self.bounds), (right, self.bounds)),
            ((0, top - self.bounds), (right, top - self.bounds))
        ]
        print('lines')
        print(lines)
        return lines

    def _largest(self, matches):
        """
        Detect the largest of each match from the vision software
        :param matches:
        :return: (x, y, w, h) match
        """
        largest = 0
        if matches is not None:
            for key in matches:
                if self.vision.get_area(matches[key]) > self.vision.get_area(matches[largest]):
                    largest = key

            return matches[largest]
        return None

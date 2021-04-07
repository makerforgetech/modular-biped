from pubsub import pub

class Tracking:
    def __init__(self, vision, bounds_percent=10, **kwargs):
        self.vision = vision
        # define bounds around screen
        self.bounds_percent = bounds_percent
        self.bounds = int(self.vision.dimensions[0] / (100 / bounds_percent))
        self.vision.add_lines(self._define_boundary_lines())
        self.ignore = 0
        self.active = kwargs.get('active', False)
        pub.subscribe(self.loop, 'loop')

    def loop(self):
        if not self.active:
            return
        self.track_largest_match()

    def track_largest_match(self):
        """
        Move the pan and tilt servos an incremental amount to attempt to keep the largest match
        within the defined bounds on screen

        Incremental amount is the percentage of the screen defined as boundary
        :return: boolean - was match detected
        """
        largest = self._largest(self.vision.detect())
        if largest is None:
            return False

        # Run through the buffer to ignore cached matches
        if self.ignore > 0:
            self.ignore = self.ignore -1
            return True
        
        (x, y, w, h) = largest
        moved = False
        if x < self.bounds:
            pub.sendMessage('servo:pan:mv', percentage=self.bounds_percent)
            moved = True
        elif (x + w) > (self.vision.dimensions[0] - self.bounds):
            pub.sendMessage('servo:pan:mv', percentage=-self.bounds_percent)
            moved = True
        if (y + h) > (self.vision.dimensions[1] - self.bounds):
            pub.sendMessage('servo:tilt:mv', percentage=self.bounds_percent)
            moved = True
        elif y < self.bounds:
            pub.sendMessage('servo:tilt:mv', percentage=-self.bounds_percent)
            moved = True

        if moved:
            self.vision.reset()
            self.ignore = 5

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

from pubsub import pub
from threading import Thread

class Tracking:
    def __init__(self, vision, bounds_percent=10, **kwargs):
        self.vision = vision
        # define bounds around screen
        self.bounds_percent = bounds_percent
        self.move_percent = bounds_percent
        self.bounds = int(self.vision.dimensions[0] / (100 / bounds_percent))
        self.vision.add_lines(self._define_boundary_lines())
        self.ignore = 0
        self.active = kwargs.get('active', False)

        self.use_thread = kwargs.get('thread', True) # Faster but uses max resources

        if not self.use_thread:
            pub.subscribe(self.loop, 'loop')
        pub.subscribe(self.set_state, 'rest', active=True)
        pub.subscribe(self.set_state, 'wake', active=True)
        pub.subscribe(self.set_state, 'sleep', active=False)
        pub.subscribe(self.set_state, 'exit', active=False)

    def set_state(self, active):
        self.active = active
        if active and self.use_thread:
            Thread(target=self.loop_thread, args=()).start()

    def loop_thread(self):
        """
        Begin tracking largest match at maximum available speed.
        Pass 'thread=True' in kwargs to enable this
        """
        while self.active:
            self.track_largest_match()

    def loop(self):
        """
        Use standard application loop to track largest match. More resource efficient but slightly slower response time.
        Pass 'thread=False' to use this mode
        """
        if not self.active:
            return
        self.track_largest_match()

    def show_position(self, largest):
        """
        Show the position of the largest match in the eye LEDs
        @todo move to personality module
        """
        if largest is None:
            return

        (x, y, w, h) = largest
        if x + (w / 2) < (self.vision.dimensions[0] / 2) - 40:
            pub.sendMessage('led', identifiers=['left', 'middle'], color='off')
            pub.sendMessage('led', identifiers='right', color='green')
        elif x + (w / 2) > (self.vision.dimensions[0] / 2) + 40:
            pub.sendMessage('led', identifiers=['right', 'middle'], color='off')
            pub.sendMessage('led', identifiers='left', color='green')
        else:
            pub.sendMessage('led', identifiers=['left', 'right'], color='off')
            pub.sendMessage('led', identifiers='middle', color='green')

    def track_largest_match(self):
        """
        Move the pan and tilt servos an incremental amount to attempt to keep the largest match
        within the defined bounds on screen

        Incremental amount is the percentage of the screen defined as boundary
        :return: boolean - was match detected
        """
        largest = self._largest(self.vision.detect())
        self.show_position(largest)
        if largest is None:
            return False

        # Run through the buffer to ignore cached matches
        if self.ignore > 0:
            self.ignore = self.ignore -1
            return True
        
        (x, y, w, h) = largest
        moved = False
        if x < self.bounds:
            pub.sendMessage('servo:pan:mv', percentage=self.move_percent)
            pub.sendMessage('log:info', msg="[Tracking] moved left")
            moved = True
        elif (x + w) > (self.vision.dimensions[0] - self.bounds):
            pub.sendMessage('servo:pan:mv', percentage=-self.move_percent)
            pub.sendMessage('log:info', msg="[Tracking] moved right")
            moved = True
        if (y + h) > (self.vision.dimensions[1] - self.bounds):
            pub.sendMessage('servo:tilt:mv', percentage=self.move_percent)
            pub.sendMessage('servo:neck:mv', percentage=self.move_percent)
            pub.sendMessage('log:info', msg="[Tracking] moved up")
            moved = True
        elif y < self.bounds:
            pub.sendMessage('servo:tilt:mv', percentage=-self.move_percent)
            pub.sendMessage('servo:neck:mv', percentage=-self.move_percent) # move neck as well to add clearance
            pub.sendMessage('log:info', msg="[Tracking] moved down")
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

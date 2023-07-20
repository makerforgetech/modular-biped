from pubsub import pub
from threading import Thread

class Tracking:
    TRACKING_THRESHOLD = 30
    TRACKING_MOVE_PERCENT = 10

    def __init__(self, vision, **kwargs):
        self.vision = vision
        self.active = kwargs.get('active', False)
        self.use_thread = kwargs.get('thread', False) # Faster but uses max resources

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

    def track_largest_match(self):
        """
        Move the pan and tilt servos an incremental amount to attempt to keep the largest match
        within the defined bounds on screen

        Incremental amount is the percentage of the screen defined as boundary
        :return: boolean - was match detected
        """
        largest = self._largest(self.vision.detect())
        pub.sendMessage('tracking:match', largest=largest, screen=self.vision.dimensions)
        if largest is None:
            return False

        (x, y, w, h) = largest

        x_move = Tracking.calc_move_amount(self.vision.dimensions[0], x, w)
        y_move = Tracking.calc_move_amount(self.vision.dimensions[1], y, h)

        if x_move:
            pub.sendMessage('servo:pan:mv', percentage=x_move)
            pub.sendMessage('log:info', msg="[Tracking] panning " + str(x_move) + "%")
        if y_move:
            pub.sendMessage('servo:tilt:mv', percentage=-y_move)
            pub.sendMessage('log:info', msg="[Tracking] tilting " + str(-y_move) + "% and moving neck " + str(y_move) + "%")
        return True

    @staticmethod
    def calc_move_amount(screen_w, target_pos, target_w):
        screen_c = screen_w / 2
        target_c = target_pos + (target_w / 2)
        # For X, 270 = far sides
        if abs(screen_c - target_c) > Tracking.TRACKING_THRESHOLD:
            return round((screen_c - target_c) / Tracking.TRACKING_MOVE_PERCENT)
        return 0

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

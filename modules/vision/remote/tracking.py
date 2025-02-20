from pubsub import pub
from threading import Thread

class Tracking:
    TRACKING_THRESHOLD = 30
    TRACKING_MOVE_PERCENT = 10

    def __init__(self, vision, **kwargs):
        self.vision = vision
        self.active = kwargs.get('active', False)
        self.use_thread = kwargs.get('thread', False)
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
        while self.active:
            self.track_largest_match()

    def loop(self):
        if not self.active:
            return
        self.track_largest_match()

    def track_largest_match(self):
        largest = self._largest(self.vision.detect())
        pub.sendMessage('tracking:match', largest=largest, screen=getattr(self.vision, 'dimensions', (640,480)))
        if largest is None:
            return False
        (x, y, w, h) = largest
        x_move = Tracking.calc_move_amount(getattr(self.vision, 'dimensions', (640,))[0], x, w)
        y_move = Tracking.calc_move_amount(getattr(self.vision, 'dimensions', (480,))[0], y, h)
        if x_move:
            pub.sendMessage('servo:pan:mv', percentage=x_move)
        if y_move:
            pub.sendMessage('servo:tilt:mv', percentage=-y_move)
        return True

    @staticmethod
    def calc_move_amount(screen_w, target_pos, target_w):
        screen_c = screen_w / 2
        target_c = target_pos + (target_w / 2)
        if abs(screen_c - target_c) > Tracking.TRACKING_THRESHOLD:
            return round((screen_c - target_c) / Tracking.TRACKING_MOVE_PERCENT)
        return 0

    def _largest(self, matches):
        largest = None
        if matches:
            for match in matches:
                if largest is None or self.vision.get_area(match) > self.vision.get_area(largest):
                    largest = match
            return largest
        return None

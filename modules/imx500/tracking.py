import asyncio
from pubsub import pub
from threading import Thread
from time import sleep

class Tracking:
    TRACKING_THRESHOLD = (10, 10)
    CAMERA_FOV = (60, 40)  # Field of view of camera
    VIDEO_SIZE = (640, 480)  # Pixel dimensions of the image
    VIDEO_CENTER = (VIDEO_SIZE[0] / 2, VIDEO_SIZE[1] / 2)
    DEG_PER_PIXEL = (CAMERA_FOV[0] / VIDEO_SIZE[0], CAMERA_FOV[1] / VIDEO_SIZE[1])
    SERVO_RANGE_DEG = (160, 120)
    
    def __init__(self, **kwargs):
        self.active = kwargs.get('active', True)
        self.moving = False

        # Subscribe to vision and servo-related topics
        pub.subscribe(self.handle, 'vision:detections')
        pub.subscribe(self.set_state, 'rest', active=True)
        pub.subscribe(self.set_state, 'wake', active=True)
        pub.subscribe(self.set_state, 'sleep', active=False)
        pub.subscribe(self.set_state, 'exit', active=False)

    def set_state(self, active):
        """Set the tracking state (active/inactive)."""
        self.active = active

    def debounce(self, movement_duration):
        """Custom debounce based on movement duration."""
        sleep(movement_duration)
        self.moving = False

    async def process_matches(self, matches):
        """Asynchronously process matches and track the largest."""
        people = self.filter_by_category(matches, 'person')
        if len(people) > 0:
            self.track_closest_to_center(people)

    def handle(self, matches):
        """Handle new detections by processing in an asynchronous thread."""
        if not self.active or self.moving:
            return
        asyncio.run(self.process_matches(matches))

    @staticmethod
    def filter_by_category(objects, category):
        """Filter detections by the specified category (e.g., 'person')."""
        return [obj for obj in objects if obj['category'] == category]

    def track_closest_to_center(self, matches):
        """Track the object closest to the center of the screen."""
        def distance_from_center(match):
            (x, y, x2, y2) = match['bbox']
            center_x = (x + x2) / 2
            center_y = (y + y2) / 2
            return abs(center_x - Tracking.VIDEO_CENTER[0]) + abs(center_y - Tracking.VIDEO_CENTER[1])

        closest_match = min(matches, key=distance_from_center)
        self.track_largest_match([closest_match])

    def track_largest_match(self, matches):
        """Move servos to track the largest match on the screen."""
        largest = self._largest(matches)
        if largest is None or self.moving:
            return False

        self.moving = True

        (x, y, x2, y2) = largest['bbox']
        x_move = self.calc_move_amount_from_dist(0, largest['distance_x'])
        y_move = self.calc_move_amount_from_dist(1, largest['distance_y'])
        
        if x_move:
            pub.sendMessage('servo:pan:mv', percentage=x_move)
        if y_move:
            pub.sendMessage('servo:tilt:mv', percentage=y_move)

        move_time = abs(max(x_move, y_move)) / 5
        stop_moving = Thread(target=self.debounce, args=(move_time,))
        stop_moving.start()

        return True

    @staticmethod
    def calc_move_amount_from_dist(axis, distance):
        """Calculate how much to move the servo based on distance."""
        if abs(distance) <= Tracking.TRACKING_THRESHOLD[axis]:
            return 0
        
        difference_deg = distance * Tracking.DEG_PER_PIXEL[axis]
        move_pc = round(difference_deg / Tracking.SERVO_RANGE_DEG[axis] * 50)  # Reduced for finer control
        return move_pc

    def _largest(self, matches):
        """Detect and return the largest match."""
        return max(matches, key=lambda m: self._get_area(m['bbox']), default=None)

    @staticmethod
    def _get_area(bbox):
        """Calculate the area of the bounding box."""
        if bbox is not None:
            x, y, x2, y2 = bbox
            return float(x2 - x) * float(y2 - y)
        return 0


if __name__ == "__main__":
    from picamimx500 import PiCamImx500
    mycam = PiCamImx500()
    tracking = Tracking()

    while True:
        mycam.scan(1)

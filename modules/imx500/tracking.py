import asyncio
from pubsub import pub
from threading import Thread
from time import sleep

class Tracking:
    TRACKING_THRESHOLD = (50, 50)
    VIDEO_SIZE = (640, 480)  # Pixel dimensions of the image
    VIDEO_CENTER = (VIDEO_SIZE[0] / 2, VIDEO_SIZE[1] / 2)
    PIXELS_PER_DEG = (-12.5, 5.5) # Set during calibration session. Run calibrate_servo_movement() to recalibrate

    def __init__(self, **kwargs):
        self.active = kwargs.get('active', True)
        self.moving = False
        self.camera = kwargs.get('camera', None)
        self.filter = kwargs.get('filter', 'person')

        # Subscribe to vision and servo-related topics
        pub.subscribe(self.handle, 'vision:detections')
        pub.subscribe(self.unfreeze, 'vision:stable')
        pub.subscribe(self.set_state, 'rest', active=True)
        pub.subscribe(self.set_state, 'wake', active=True)
        pub.subscribe(self.set_state, 'sleep', active=False)
        pub.subscribe(self.set_state, 'exit', active=False)

    def set_state(self, active):
        """Set the tracking state (active/inactive)."""
        self.active = active
        
    def unfreeze(self):
        self.moving = False

    # def debounce(self, movement_duration):
    #     """Custom debounce based on movement duration."""
    #     sleep(movement_duration)
    #     self.moving = False

    async def process_matches(self, matches):
        """Asynchronously process matches and track the largest."""
        filtered = self.filter_by_category(matches, self.filter)
        if len(filtered) > 0:
            self.track_closest_to_center(filtered)

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
        self.track_match(largest)
        
    def track_match(self, match):

        (x, y, x2, y2) = match['bbox']
        x_move = self.calc_move_amount_from_dist(0, match['distance_x'])
        y_move = self.calc_move_amount_from_dist(1, match['distance_y'])
        
        print(f"Moving X:  {x_move} ({match['distance_x']})")
        print(f"Moving Y:  {y_move} ({match['distance_y']})")
        
        if x_move:
            pub.sendMessage('servo:pan:mv', percentage=x_move)
        if y_move:
            pub.sendMessage('servo:tilt:mv', percentage=y_move)

        # move_time = max(abs(max(x_move, y_move)) / 50, 1) # min 1 second
        # print(f"Move time: {move_time}")
        # stop_moving = Thread(target=self.debounce, args=(move_time,))
        # stop_moving.start()

        return True

    @staticmethod
    def calc_move_amount_from_dist(axis, distance):
        """Calculate how much to move the servo based on distance."""
        if abs(distance) <= Tracking.TRACKING_THRESHOLD[axis]:
            return 0
        
        difference_deg = distance / Tracking.PIXELS_PER_DEG[axis]
        return difference_deg

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
    tracking = Tracking(camera=mycam)

    while True:
        mycam.scan()

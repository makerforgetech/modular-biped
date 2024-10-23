import asyncio
from pubsub import pub
from threading import Thread
from time import sleep

class Tracking:
    TRACKING_THRESHOLD = (50, 50)
    VIDEO_SIZE = (640, 480)  # Pixel dimensions of the image
    VIDEO_CENTER = (VIDEO_SIZE[0] / 2, VIDEO_SIZE[1] / 2)
    PIXELS_PER_DEG = (-12.5, 0.7) # Set during calibration session. Run calibrate_servo_movement() to recalibrate

    def __init__(self, **kwargs):
        self.active = kwargs.get('active', True)
        self.moving = False
        self.camera = kwargs.get('camera', None)
        self.filter = kwargs.get('filter', 'person')

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
        # if y_move:
            # pub.sendMessage('servo:tilt:mv', percentage=y_move)

        move_time = max(abs(max(x_move, y_move)) / 50, 1) # min 1 second
        print(f"Move time: {move_time}")
        stop_moving = Thread(target=self.debounce, args=(move_time,))
        stop_moving.start()

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

    def calibrate_servo_movement(self, axis=0, label=None, match=None, servo_move_pct=10):
        """
        Calibrate the servos to determine the degree range for pan (x-axis) and tilt (y-axis).
        Moves the servo a preset percentage, then calculates the degree-per-pixel ratio.
        
        :param match: The match (object) to track.
        :param servo_move_pct: Percentage of the servo's range to move for calibration.
        """
        match = self._get_a_match(label)
            
        if match == None:
            print('Could not find match, skipping calibration')
            return
        # Get the initial position of the object
        # (x, y, x2, y2) = match['bbox']
        # initial_center_x = (x + x2) / 2
        # initial_center_y = (y + y2) / 2
        
        # Move the servos a preset percentage
        if axis == 0:
            pub.sendMessage('servo:pan:mv', percentage=servo_move_pct)
        else:
            pub.sendMessage('servo:tilt:mv', percentage=servo_move_pct)

        # Wait for the servo movement to complete (e.g., debounce time)
        sleep(5)  # This can be adjusted as per servo speed
        
        # Re-detect the object after the movement
        new_match = None
        for i in range(5):
            new_matches = self._get_latest_detections()
            if len(new_matches) > 0:
                new_match = self._find_same_match(new_matches, match)

        if new_match:
            # Get the new position of the object
            # (nx, ny, nx2, ny2) = new_match['bbox']
            # new_center_x = (nx + nx2) / 2
            # new_center_y = (ny + ny2) / 2

            # Calculate the pixel movement
            # if axis == 0:
            #     pixel_movement = new_center_x - initial_center_x
            # else:
            #     pixel_movement = new_center_y - initial_center_y

            # Calculate the degrees moved
            # pixels_per_percent = pixel_movement / servo_move_pct
            if axis == 0:
                dist = match['distance_x'] - new_match['distance_x']
            else:
                dist = match['distance_y'] - new_match['distance_y']
            dist_ppc = dist / servo_move_pct
            
            newvals = list(Tracking.PIXELS_PER_DEG)
            newvals[axis] = dist_ppc
            Tracking.PIXELS_PER_DEG = tuple(newvals)
            
            # print(f"Initial Dist: {match['distance_x']}, New Dist: {new_match['distance_x']}, Diff: {dist}, Px/%: {dist_ppc}")
            # print(f'Initial: {initial_center_x}, New: {new_center_x}, Diff: {pixel_movement}, Px/%: {pixels_per_percent}')
            
            print(f"Calibration complete: New PIXELS_PER_DEG assigned for axis {axis}. values: {Tracking.PIXELS_PER_DEG}")
            
        else:
            print('No second match to calibrate against!')
            
            
    def _get_a_match(self, label):
        for i in range(5):
            matches = self._get_latest_detections()
            if len(matches) > 0:
                for m in matches:
                    if m['category'] == label:
                        return m 

    def _get_latest_detections(self):
        return self.camera.scan(1)

    def _find_same_match(self, matches, original_match):
        """
        Find the same object in the new detection list based on bounding box similarity.
        This helps track the object after servo movement.
        """
        def is_similar_bbox(bbox1, bbox2, threshold=0.2):
            # Compare bounding boxes; use some threshold for similarity
            (x1, y1, x2_1, y2_1) = bbox1
            (x2, y2, x2_2, y2_2) = bbox2
            return abs(x1 - x2) < threshold * Tracking.VIDEO_SIZE[0] and \
                   abs(y1 - y2) < threshold * Tracking.VIDEO_SIZE[1]

        for match in matches:
            if original_match['category'] == match['category'] or is_similar_bbox(original_match['bbox'], match['bbox']):
                return match
        return None


if __name__ == "__main__":
    from picamimx500 import PiCamImx500
    mycam = PiCamImx500()
    tracking = Tracking(camera=mycam)

    # Calibrate the servo range with a sample match
    tracking.calibrate_servo_movement(0)
    tracking.calibrate_servo_movement(1)

    while True:
        mycam.scan(1)

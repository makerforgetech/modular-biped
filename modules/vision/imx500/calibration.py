from pubsub import pub
from time import sleep
from .tracking import Tracking

"""
To enable, disable tracking.active, import into main.py and pass the vision and tracking instances from ModuleLoader.
"""
class Calibration:
    def __init__(self, vision, tracking):
        self.vision = vision
        self.tracking = tracking
        
        self.calibrate_servo_movement(0, 'tv')
        self.calibrate_servo_movement(1, 'tv', None, 30)
        sleep(2)
        tracking.active = True
        
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
        return self.vision.scan()

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
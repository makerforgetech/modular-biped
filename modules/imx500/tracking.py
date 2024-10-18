from pubsub import pub
from threading import Thread, Timer
from time import sleep
import cv2, json
class Tracking:
    TRACKING_THRESHOLD = (10, 10)

    # MATCH_IDS = [0, 17, 18] # The Id of objects to pay attention to: {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'n/a', 12: 'stop sign', 13: 'parking meter', 14: 'bench', 15: 'bird', 16: 'cat', 17: 'dog', 18: 'horse', 19: 'sheep', 20: 'cow', 21: 'elephant', 22: 'bear', 23: 'zebra', 24: 'giraffe', 25: 'n/a', 26: 'backpack', 27: 'umbrella', 28: 'n/a', 29: 'n/a', 30: 'handbag', 31: 'tie', 32: 'suitcase', 33: 'frisbee', 34: 'skis', 35: 'snowboard', 36: 'sports ball', 37: 'kite', 38: 'baseball bat', 39: 'baseball glove', 40: 'skateboard', 41: 'surfboard', 42: 'tennis racket', 43: 'bottle', 44: 'n/a', 45: 'wine glass', 46: 'cup', 47: 'fork', 48: 'knife', 49: 'spoon', 50: 'bowl', 51: 'banana', 52: 'apple', 53: 'sandwich', 54: 'orange', 55: 'broccoli', 56: 'carrot', 57: 'hot dog', 58: 'pizza', 59: 'donut', 60: 'cake', 61: 'chair', 62: 'couch', 63: 'potted plant', 64: 'bed', 65: 'n/a', 66: 'dining table', 67: 'n/a', 68: 'n/a', 69: 'toilet', 70: 'n/a', 71: 'tv', 72: 'laptop', 73: 'mouse', 74: 'remote', 75: 'keyboard', 76: 'cell phone', 77: 'microwave', 78: 'oven', 79: 'toaster', 80: 'sink', 81: 'refrigerator', 82: 'n/a', 83: 'book', 84: 'clock', 85: 'vase', 86: 'scissors', 87: 'teddy bear', 88: 'hair drier', 89: 'toothbrush'}
    
    # For calculating movements 
    CAMERA_FOV = (60, 40) # Field of view of camera (used to calculate amount of movement in each tracking operation)
    VIDEO_SIZE = (640, 480) # Pixel dimensions of image
    VIDEO_CENTER = (VIDEO_SIZE[0]/2, VIDEO_SIZE[1]/2)
    DEG_PER_PIXEL = (CAMERA_FOV[0] / VIDEO_SIZE[0], CAMERA_FOV[1] / VIDEO_SIZE[1])
    SERVO_RANGE_DEG = (160, 120)
    DEBOUNCE_TIME = 5
    def __init__(self, **kwargs):
        self.active = kwargs.get('active', True)

        pub.subscribe(self.handle, 'vision:detections')
        pub.subscribe(self.set_state, 'rest', active=True)
        pub.subscribe(self.set_state, 'wake', active=True)
        pub.subscribe(self.set_state, 'sleep', active=False)
        pub.subscribe(self.set_state, 'exit', active=False)

        self.moving = False

    def set_state(self, active):
        self.active = active

    def debounce(self):
        self.moving = False

    def handle(self, matches):
        """
        Use standard application loop to track largest match. More resource efficient but slightly slower response time.
        Pass 'thread=False' to use this mode
        """
        # print(matches)
        #[{'category': 'chair', 'confidence': '0.62109375', 'bbox': (40, 315, 225, 163)}, {'category': 'tv', 'confidence': '0.5625', 'bbox': (39, 192, 176, 125)}]
        
            
        if not self.active:
            return
        people = Tracking.filter_by_category(matches, 'person')
        if len(people) > 0:
            # print('Tracking people only!')
            matches = people
        else:
            return
        self.track_largest_match(matches)
        
    @staticmethod
    def filter_by_category(objects, category):
        """
        Filters the list of objects based on the given category.

        Args:
        objects (list): List of dictionaries containing object details.
        category (str): The category to filter by.

        Returns:
        list: A list of objects that match the specified category.
        """
        return [obj for obj in objects if obj['category'] == category]

    def track_largest_match(self, matches):
        """
        Move the pan and tilt servos an incremental amount to attempt to keep the largest match
        within the defined bounds on screen

        Incremental amount is the percentage of the screen defined as boundary
        :return: boolean - was match detected
        """
        largest = self._largest(matches, None)
        
        if largest is None or self.moving:
            return False
        self.moving = True

        (x, y, x2, y2) = largest['bbox']
        w = x2-x
        h = y2-y

        x_move = Tracking.calc_move_amount_from_dist(0, largest['distance_x'])
        y_move = Tracking.calc_move_amount_from_dist(1, largest['distance_y'])
        print(x_move, y_move)

        if x_move:
            pub.sendMessage('servo:pan:mv', percentage=x_move)
            pub.sendMessage('log:info', msg="[Tracking] panning " + str(x_move) + "%")
        if y_move:
            pub.sendMessage('servo:tilt:mv', percentage=y_move)
            pub.sendMessage('log:info', msg="[Tracking] tilting " + str(y_move) + "%")
        
        #stop_moving = Timer(abs(max(x_move,y_move))/5, self.debounce) # Wait for some time depending on amount of movement
        stop_moving = Timer(Tracking.DEBOUNCE_TIME, self.debounce) # Wait for 2 seconds until this behaviour is improved. Then time can be reduced.
        stop_moving.start()

        return True

    @staticmethod
    def calc_move_amount_from_dist(axis, distance):

        # Calculate difference between screen_c and target_c in pixels
        if abs(distance) <= Tracking.TRACKING_THRESHOLD[axis]:
            return 0
        
        # Translate to degrees using preset constants
        difference_deg = distance * Tracking.DEG_PER_PIXEL[axis]
        # print('difference_deg: ' + str(difference_deg))

        # Set servo relative position as percentage of range.
        move_pc = round(difference_deg / Tracking.SERVO_RANGE_DEG[axis] * 100)
        # print(str(axis) + ' move_pc: ' + str(move_pc))
        return move_pc
    
    @staticmethod
    def calc_move_amount_variable(axis, target_pos, target_w):

        target_c = target_pos + (target_w / 2)
        # print('target_c: ' + str(target_c))
        # print('screen_c: ' + str(Tracking.VIDEO_CENTER[axis]))
        
        # Calculate difference between screen_c and target_c in pixels
        difference_px = (Tracking.VIDEO_CENTER[axis] - target_c)
        # print('difference_px: ' + str(difference_px))
        if abs(difference_px) <= Tracking.TRACKING_THRESHOLD[axis]:
            return 0
        
        # Translate to degrees using preset constants
        difference_deg = difference_px * Tracking.DEG_PER_PIXEL[axis]
        # print('difference_deg: ' + str(difference_deg))

        # Set servo relative position as percentage of range.
        move_pc = round(difference_deg / Tracking.SERVO_RANGE_DEG[axis] * 100)
        # print(str(axis) + ' move_pc: ' + str(move_pc))
        return move_pc

    def _largest(self, matches, ids_to_track):
        """
        Detect the largest of each match from the vision software
        :param matches:
        :return: (x, y, w, h) match
        """
        largest = None
        if matches is not None:
            for match in matches:
                if ids_to_track is not None and match.id not in ids_to_track:
                    continue
                print(match)
                if largest is None or self._get_area(match['bbox']) > self._get_area(largest['bbox']):
                    # if area is larger than 50% of the screen, ignore it
                    if self._get_area(match['bbox']) > (Tracking.VIDEO_SIZE[0] * Tracking.VIDEO_SIZE[1] * 0.5):
                        continue
                    largest = match
            return largest
        return None

    def _get_area(self, match):
        """
        Wrapper to return area calculation.
        Deliberately not a static method so that it can be accessed via dependency injection
        :param match: cv2 match
        :return: area calcualation
        """
        if match is not None:
            x, y, x2, y2 = match
            return float(x2-x) * float(y2-y)
        return 0


if __name__ == "__main__":
    from picamimx500 import PiCamImx500
    mycam = PiCamImx500()
    tracking = Tracking()
    
    while True:
        mycam.scan(1)
        

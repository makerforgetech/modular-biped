from pubsub import pub
from threading import Thread, Timer

class Tracking:
    TRACKING_THRESHOLD = 50
    TRACKING_MOVE_PERCENT = 10 # Larger number = smaller movement

    MATCH_PERSON_ID = 0 # The Id of the 'person object': {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'n/a', 12: 'stop sign', 13: 'parking meter', 14: 'bench', 15: 'bird', 16: 'cat', 17: 'dog', 18: 'horse', 19: 'sheep', 20: 'cow', 21: 'elephant', 22: 'bear', 23: 'zebra', 24: 'giraffe', 25: 'n/a', 26: 'backpack', 27: 'umbrella', 28: 'n/a', 29: 'n/a', 30: 'handbag', 31: 'tie', 32: 'suitcase', 33: 'frisbee', 34: 'skis', 35: 'snowboard', 36: 'sports ball', 37: 'kite', 38: 'baseball bat', 39: 'baseball glove', 40: 'skateboard', 41: 'surfboard', 42: 'tennis racket', 43: 'bottle', 44: 'n/a', 45: 'wine glass', 46: 'cup', 47: 'fork', 48: 'knife', 49: 'spoon', 50: 'bowl', 51: 'banana', 52: 'apple', 53: 'sandwich', 54: 'orange', 55: 'broccoli', 56: 'carrot', 57: 'hot dog', 58: 'pizza', 59: 'donut', 60: 'cake', 61: 'chair', 62: 'couch', 63: 'potted plant', 64: 'bed', 65: 'n/a', 66: 'dining table', 67: 'n/a', 68: 'n/a', 69: 'toilet', 70: 'n/a', 71: 'tv', 72: 'laptop', 73: 'mouse', 74: 'remote', 75: 'keyboard', 76: 'cell phone', 77: 'microwave', 78: 'oven', 79: 'toaster', 80: 'sink', 81: 'refrigerator', 82: 'n/a', 83: 'book', 84: 'clock', 85: 'vase', 86: 'scissors', 87: 'teddy bear', 88: 'hair drier', 89: 'toothbrush'}
    
    # For calculating movements 
    CAMERA_FOV = 160 # Field of view of camera
    VIDEO_SIZE = (640, 480) # Pixel dimensions of image
    SCREEN_X_C = VIDEO_SIZE[0] / 2 # Center of screen
    DEG_PER_PIXEL = VIDEO_SIZE[0] / CAMERA_FOV # Calculate number of degrees in each pixel 
    PAN_RANGE_DEG = 180 # Define range in degrees of pan camera

    def __init__(self, **kwargs):
        self.active = kwargs.get('active', False)

        pub.subscribe(self.handle, 'vision:matches')
        pub.subscribe(self.set_state, 'rest', active=True)
        pub.subscribe(self.set_state, 'wake', active=True)
        pub.subscribe(self.set_state, 'sleep', active=False)
        pub.subscribe(self.set_state, 'exit', active=False)

        self.moving = False

    def set_state(self, active):
        self.active = active

    def debounce(self):
        self.moving = False

    def handle(self, matches, labels):
        """
        Use standard application loop to track largest match. More resource efficient but slightly slower response time.
        Pass 'thread=False' to use this mode
        """
        if not self.active:
            return
        self.track_largest_match(matches, labels)

    def track_largest_match(self, matches, labels):
        """
        Move the pan and tilt servos an incremental amount to attempt to keep the largest match
        within the defined bounds on screen

        Incremental amount is the percentage of the screen defined as boundary
        :return: boolean - was match detected
        """
        # print('matches sent to Tracking')
        # print(matches)
        largest = self._largest(matches, Tracking.MATCH_PERSON_ID)
        # pub.sendMessage('tracking:match', largest=largest, screen=self.vision.dimensions)
        if largest is None:# or self.moving:
            return False

        self.moving = True

        (x, y, x2, y2) = largest.bbox
        w = x2-x
        h = y2-y

        x_move = Tracking.calc_move_amount_pan(x, w)
        y_move = Tracking.calc_move_amount(Tracking.VIDEO_SIZE[1], y, h)

        if x_move:
            pub.sendMessage('servo:pan:mv', percentage=-x_move)
            pub.sendMessage('log:info', msg="[Tracking] panning " + str(x_move) + "%")
        if y_move:
            pub.sendMessage('servo:tilt:mv', percentage=-y_move)
            pub.sendMessage('servo:neck:mv', percentage=y_move)
            pub.sendMessage('log:info', msg="[Tracking] tilting " + str(-y_move) + "% and moving neck " + str(y_move) + "%")
        
        stop_moving = Timer(.5, self.debounce)
        stop_moving.start()

        return True

    @staticmethod
    def calc_move_amount_pan(target_pos, target_w):
        target_c = target_pos + (target_w / 2)

        # 1. Get number of degrees visible by camera CAMERA_FOV
        # 2. Get number of pixels in image VIDEO_SIZE
        # 3. Calculate degrees per pixel DEG_PER_PIXEL
        # 4. Calculate difference between screen_c and target_c in pixels
        difference_px = (Tracking.SCREEN_X_C - target_c)
        print('difference_px')
        print(difference_px)
        # 5. Translate to degrees using above values
        difference_deg = difference_px / Tracking.DEG_PER_PIXEL
        # 6. Identify range of servo in degrees
        PAN_RANGE_DEG = 180
        # 7. Set servo relative position as percentage of range.
        if difference_deg == 0:
            return 0
        print('difference_deg')
        print(difference_deg)
        move_pc = round(difference_deg / PAN_RANGE_DEG * 100)

        return move_pc

    @staticmethod
    def calc_move_amount(screen_w, target_pos, target_w):
        screen_c = screen_w / 2
        target_c = target_pos + (target_w / 2)
        # For X, 270 = far sides
        if abs(screen_c - target_c) > Tracking.TRACKING_THRESHOLD:
            if screen_c > target_c:
                return 2 # temp - move a bit each frame rather than trying to jump
            return -2
            # return round((screen_c - target_c) / Tracking.TRACKING_MOVE_PERCENT)
        return 0

    def _largest(self, matches, id_to_track):
        """
        Detect the largest of each match from the vision software
        :param matches:
        :return: (x, y, w, h) match
        """
        largest = None
        if matches is not None:
            for match in matches:
                if largest is None or (match.id == id_to_track and self._get_area(match.bbox) > self._get_area(largest.bbox)):
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

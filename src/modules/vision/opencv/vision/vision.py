import argparse
import sys
import cv2
import numpy as np
from functools import lru_cache

from modules.base_module import BaseModule

# Add picamera2 imports
from picamera2 import Picamera2, Preview

class Detection:
    def __init__(self, box, conf, selfref):
        self.box = box  # (x, y, w, h)
        self.conf = conf
        self.piCamImx500 = selfref
        # Calculate distances from center (assume 640x480 frame)
        x, y, w, h = self.box
        detection_center_x = x + w // 2
        detection_center_y = y + h // 2
        screen_center_x = 640 // 2
        screen_center_y = 480 // 2
        self.distance_x = int(detection_center_x - screen_center_x)
        self.distance_y = int(detection_center_y - screen_center_y)

    def display(self):
        label = f"face ({self.conf:.2f}): {self.box}"
        print(label)
        print("")

    def json_out(self):
        return {
            'category': 'person',
            'confidence': str(self.conf),
            'bbox': list(map(int, self.box)),
            'distance_x': self.distance_x,
            'distance_y': self.distance_y,
        }

class Vision(BaseModule):
    def __init__(self, **kwargs):
        """
        Simple face detection using OpenCV Haar cascades.
        Dependencies: opencv-python, numpy, modules.base_module, picamera2
        """
        self.last_detections = []
        self.last_results = []
        self.args = Vision.get_args()
        # Use OpenCV's built-in Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        # Use PiCamera2 instead of VideoCapture
        cam_index = getattr(self.args, "camera", 0)
        # Select camera if multiple are present
        self.picam2 = Picamera2(camera_num=cam_index)
        self.picam2.configure(self.picam2.create_preview_configuration(main={"format": 'RGB888', "size": (640, 480)}))
        self.picam2.start()
        # Stabilization state
        self.previous_frame = None
        self.stable_frame_count = 0
        self.moving = False

    def setup_messaging(self):
        pass

    def loop(self):
        """Called every system loop cycle to run object detection."""
        self.scan()

    def scan(self):
        self.last_results = self.parse_detections()
        this_capture = [obj.json_out() for obj in self.last_results]
        self.publish('vision/detections', matches=this_capture)
        return this_capture

    def parse_detections(self):
        self.last_detections = []
        # Stabilization check
        if not self.calculate_stabilization():
            self.moving = True
            return self.last_detections
        elif self.moving:
            self.moving = False
            self.publish('vision/stable')
        # Capture frame from PiCamera2
        try:
            frame = self.picam2.capture_array()
        except Exception as e:
            raise Exception(f"Failed to read frame from camera: {e}")
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )
        # print(f"Found {len(faces)} faces")s
        for (x, y, w, h) in faces:
            # Haar cascades don't provide confidence, so use 1.0
            self.last_detections.append(Detection((x, y, w, h), 1.0, self))
        return self.last_detections

    def calculate_stabilization(self, threshold=0.70, stable_frames_required=8):
        """
        Calculate if the image has stabilized based on frame differences.
        Stability is defined as the average pixel difference between consecutive frames
        being below a given threshold for a certain number of frames.
        :param threshold: Percentage of pixels that must remain stable (default 70%).
        :param stable_frames_required: Number of consecutive stable frames to confirm stabilization.
        :return: Boolean indicating if the image is stable.
        """
        try:
            current_frame = self.picam2.capture_array()
        except Exception:
            return False

        if self.previous_frame is None:
            self.previous_frame = current_frame
            return False

        frame_diff = cv2.absdiff(current_frame, self.previous_frame)
        gray_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)
        non_zero_count = np.count_nonzero(gray_diff)
        total_pixels = gray_diff.size
        diff_percentage = non_zero_count / total_pixels

        self.previous_frame = current_frame

        if diff_percentage < threshold:
            self.stable_frame_count += 1
        else:
            self.stable_frame_count = 0

        if self.stable_frame_count >= stable_frames_required:
            return True

        return False

    @lru_cache
    def get_labels(self):
        return ["face"]

    def draw_detections(self, frame, detections):
        for detection in detections:
            x, y, w, h = detection.box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"face ({detection.conf:.2f})"
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        return frame

    @staticmethod
    def get_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("--camera", type=int, default=0, help="Camera device index (e.g. 0 for /dev/video0)")
        # No model argument needed for Haar cascade
        return parser.parse_args()

if __name__ == "__main__":
    mycam = Vision()
    while True:
        detections = mycam.scan()
        # Optionally display the detections in a window
        try:
            frame = mycam.picam2.capture_array()
        except Exception:
            break
        frame = mycam.draw_detections(frame, mycam.last_results)
        cv2.imshow("Face Detection", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    mycam.picam2.stop()
    cv2.destroyAllWindows()

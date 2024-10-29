import argparse
import sys
from functools import lru_cache

import cv2, json
import numpy as np

from picamera2 import MappedArray, Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import (NetworkIntrinsics,
                                      postprocess_nanodet_detection)
from libcamera import Transform

from pubsub import pub


class Detection:
    def __init__(self, imx500, picam2, selfref, coords, category, conf, metadata):
        """Create a Detection object, recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)
        self.piCamImx500 = selfref
        self.calculate_detection_distances(320, 240)

    def calculate_detection_distances(self, screen_center_x, screen_center_y):
        """Calculate and store the X and Y distances for a detection."""
        # Extract the bounding box values (x, y, width, height)
        x, y, x2, y2 = self.box

        # Calculate the center of the detection box
        detection_center_x = x + x2 // 2
        
        # Calculate the position at the top 20% of the bounding box for Y-axis
        box_height = y2 - y
        detection_top_20_y = y + int(0.2 * box_height)
        #detection_center_y = y + y2 // 2

        # Calculate the distances between detection center and screen center
        distance_x = int(detection_center_x - screen_center_x)
        distance_y = int(detection_top_20_y - screen_center_y)

        # Store distances in the detection object
        self.distance_x = distance_x
        self.distance_y = distance_y
        
    def display(self):
        label = f"{self.piCamImx500.get_labels()[int(self.category)]} ({self.conf:.2f}%): {self.box}"
        print(label)
        print("")
    def json_out(self):
        return {
            'category': self.piCamImx500.get_labels()[int(self.category)],
            'confidence': str(self.conf),
            'bbox': self.box,
            'distance_x': self.distance_x,
            'distance_y': self.distance_y
        }
        
class Vision:
    def __init__(self, **kwargs):
        """
        Vision class
        :param kwargs: model, fps, bbox_normalization, threshold, iou, max_detections, ignore_dash_labels, postprocess, preserve_aspect_ratio, labels, print_self.intrinsics
        :param model: Path of the model
        :param fps: Frames per second
        :param bbox_normalization: Normalize bbox
        :param threshold: Detection threshold
        :param iou: Set iou threshold
        :param max_detections: Set max detections
        :param ignore_dash_labels: Remove '-' labels
        :param postprocess: Run post process of type
        :param preserve_aspect_ratio: Preserve the pixel aspect ratio of the input tensor
        :param labels: Path to the labels file
        :param print_self.intrinsics: Print JSON network_intrinsics then exit
        
        Install: pip install picamera2 libcamera
        
        Subscribes to 'loop' to scan for detections
        - Returns: list of detections
        
        Publishes to 'vision:detections' with matches
        - Argument: matches (list) - list of detections
        
        Example output:
        [
            {
                'category': 'person',
                'confidence': '0.99',
                'bbox': [0.0, 0.0, 0.0, 0.0],
                'distance_x': 0,
                'distance_y': 0
            }
        ]
        
        Example of direct use:
        mycam = Vision()
        while True:
            matches = mycam.scan()
        """
        self.last_detections = []
        self.last_results = []
        
        self.args = Vision.get_args()

        # This must be called before instantiation of Picamera2
        self.imx500 = IMX500(self.args.model)
        self.intrinsics = self.imx500.network_intrinsics
        if not self.intrinsics:
            self.intrinsics = NetworkIntrinsics()
            self.intrinsics.task = "object detection"
        elif self.intrinsics.task != "object detection":
            print("Network is not an object detection task", file=sys.stderr)
            exit()

        # Override self.intrinsics from self.args
        for key, value in vars(self.args).items():
            if key == 'labels' and value is not None:
                with open(value, 'r') as f:
                    self.intrinsics.labels = f.read().splitlines()
            elif hasattr(self.intrinsics, key) and value is not None:
                setattr(self.intrinsics, key, value)

        # Defaults
        if self.intrinsics.labels is None:
            with open("assets/coco_labels.txt", "r") as f:
                self.intrinsics.labels = f.read().splitlines()
        self.intrinsics.update_with_defaults()

        # if self.args.print_self.intrinsics:
        #     print(self.intrinsics)
        #     exit()

        self.picam2 = Picamera2(self.imx500.camera_num)
        config = self.picam2.create_preview_configuration(controls={"FrameRate": self.intrinsics.inference_rate}, buffer_count=12, transform=Transform(vflip=False, hflip=False))

        self.imx500.show_network_fw_progress_bar()
        self.picam2.start(config, show_preview=kwargs.get('preview', False))

        if self.intrinsics.preserve_aspect_ratio:
            self.imx500.set_auto_aspect_ratio()

        self.picam2.pre_callback = self.draw_detections_with_distance
        
        self.previous_frame = None
        self.stable_frame_count = 0
        self.moving = False
        
        pub.subscribe(self.scan, 'loop')

    def scan(self):
        self.last_results = self.parse_detections(self.picam2.capture_metadata())
        this_capture = []
        for i in self.last_results:
            this_capture = [obj.json_out() for obj in self.last_results]

        pub.sendMessage('vision:detections', matches=this_capture)
        return this_capture

    def parse_detections(self, metadata: dict):
        """Parse the output tensor into a number of detected objects, scaled to the ISP out."""
        
        self.last_detections = []
         # Check if the image is stable before parsing detections
        if not self.calculate_stabilization():
            # print("Image is not stable. Skipping detections.")
            self.moving = True
            return self.last_detections
        elif self.moving == True:
            self.moving = False
            pub.sendMessage('vision:stable')
    
        bbox_normalization = self.intrinsics.bbox_normalization
        threshold = self.args.threshold
        iou = self.args.iou
        max_detections = self.args.max_detections

        np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
        input_w, input_h = self.imx500.get_input_size()
        if np_outputs is None:
            return self.last_detections
        if self.intrinsics.postprocess == "nanodet":
            boxes, scores, classes = \
                postprocess_nanodet_detection(outputs=np_outputs[0], conf=threshold, iou_thres=iou,
                                            max_out_dets=max_detections)[0]
            from picamera2.devices.imx500.postprocess import scale_boxes
            boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
        else:
            boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
            if bbox_normalization:
                boxes = boxes / input_h

            boxes = np.array_split(boxes, 4, axis=1)
            boxes = zip(*boxes)

        self.last_detections = [
            Detection(self.imx500, self.picam2, self, box, category, score, metadata)
            for box, score, category in zip(boxes, scores, classes)
            if score > threshold
        ]
        return self.last_detections


    def calculate_stabilization(self, threshold=0.70, stable_frames_required=8):
        """
        Calculate if the image has stabilized based on frame differences.
        Stability is defined as the average pixel difference between consecutive frames
        being below a given threshold for a certain number of frames.
        :param threshold: Percentage of pixels that must remain stable (default 1%).
        :param stable_frames_required: Number of consecutive stable frames to confirm stabilization.
        :return: Boolean indicating if the image is stable.
        """
        current_frame = self.picam2.capture_array()

        if self.previous_frame is None:
            # If this is the first frame, store it and return False (not yet stable)
            self.previous_frame = current_frame
            return False

        # Calculate the absolute difference between the current frame and the previous frame
        frame_diff = cv2.absdiff(current_frame, self.previous_frame)

        # Convert the frame difference to grayscale for easier analysis
        gray_diff = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)

        # Calculate the percentage of pixels with significant change (non-zero value in diff)
        non_zero_count = np.count_nonzero(gray_diff)
        total_pixels = gray_diff.size
        diff_percentage = non_zero_count / total_pixels

        # Update the previous frame to be the current frame
        self.previous_frame = current_frame

        # print(diff_percentage)
        # Check if the difference is below the threshold
        if diff_percentage < threshold:
            self.stable_frame_count += 1
        else:
            self.stable_frame_count = 0

        # If the number of consecutive stable frames is greater than or equal to the required count, return True
        if self.stable_frame_count >= stable_frames_required:
            return True

        return False

    @lru_cache
    def get_labels(self):
        labels = self.intrinsics.labels

        if self.intrinsics.ignore_dash_labels:
            labels = [label for label in labels if label and label != "-"]
        return labels

    def draw_detections_with_distance(self, request, stream="main"):
        """Draw the detections for this request onto the ISP output."""
        detections = self.last_results
        if detections is None:
            return
        labels = self.get_labels()
        
        # Assuming m.array contains the frame, get the dimensions of the image to find the screen center
        with MappedArray(request, stream) as m:
            height, width, _ = m.array.shape
            screen_center_x = width // 2
            screen_center_y = height // 2

            for detection in detections:
                x, y, w, h = detection.box
                label = f"{labels[int(detection.category)]} ({detection.conf:.2f})"
                
                # Calculate the center of the detection box
                detection_center_x = x + w // 2
                detection_center_y = y + h // 2

                # Calculate the distances between detection center and screen center
                distance_x = abs(detection.distance_x)
                distance_y = abs(detection.distance_y)

                # Draw the distance as text near the detection box
                distance_label_x = f"X-Dist: {int(distance_x)} px {int(detection_center_x - screen_center_x)}"
                distance_label_y = f"Y-Dist: {int(distance_y)} px {int(detection_center_y - screen_center_y)}"

                # Text positions for the X and Y distances
                (text_width_x, text_height_x), baseline_x = cv2.getTextSize(distance_label_x, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                (text_width_y, text_height_y), baseline_y = cv2.getTextSize(distance_label_y, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                text_x = x + 5
                text_y_x = y + 30  # Below the detection box label
                text_y_y = y + 45  # Below the X-distance label

                # Create a copy of the array to draw the background with opacity
                overlay = m.array.copy()

                # Draw the background rectangles for the X and Y distance text
                cv2.rectangle(overlay,
                            (text_x, text_y_x - text_height_x),
                            (text_x + text_width_x, text_y_x + baseline_x),
                            (255, 255, 255),  # Background color (white)
                            cv2.FILLED)
                cv2.rectangle(overlay,
                            (text_x, text_y_y - text_height_y),
                            (text_x + text_width_y, text_y_y + baseline_y),
                            (255, 255, 255),  # Background color (white)
                            cv2.FILLED)

                alpha = 0.30
                cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)

                # Draw the distance text for X and Y axes
                cv2.putText(m.array, distance_label_x, (text_x, text_y_x),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                cv2.putText(m.array, distance_label_y, (text_x, text_y_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                # Draw detection box
                cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)
                
                # Draw horizontal line (X-axis)
                cv2.line(m.array, (detection_center_x, detection_center_y), (screen_center_x, detection_center_y), (0, 255, 255), 2)
                
                # Draw vertical line (Y-axis)
                cv2.line(m.array, (screen_center_x, detection_center_y), (screen_center_x, screen_center_y), (255, 0, 255), 2)

                # Calculate text size and position for detection label
                (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                text_x = x + 5
                text_y = y + 15

                # Draw background rectangle for detection label
                cv2.rectangle(overlay,
                            (text_x, text_y - text_height),
                            (text_x + text_width, text_y + baseline),
                            (255, 255, 255),  # Background color (white)
                            cv2.FILLED)

                cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)

                # Draw detection label
                cv2.putText(m.array, label, (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
            if self.intrinsics.preserve_aspect_ratio:
                b_x, b_y, b_w, b_h = self.imx500.get_roi_scaled(request)
                color = (255, 0, 0)  # red
                cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))

    @staticmethod
    def get_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("--model", type=str, help="Path of the model",
                            default="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
        parser.add_argument("--fps", type=int, help="Frames per second")
        parser.add_argument("--bbox-normalization", action=argparse.BooleanOptionalAction, help="Normalize bbox")
        parser.add_argument("--threshold", type=float, default=0.55, help="Detection threshold")
        parser.add_argument("--iou", type=float, default=0.65, help="Set iou threshold")
        parser.add_argument("--max-detections", type=int, default=10, help="Set max detections")
        parser.add_argument("--ignore-dash-labels", action=argparse.BooleanOptionalAction, help="Remove '-' labels ")
        parser.add_argument("--postprocess", choices=["", "nanodet"],
                            default=None, help="Run post process of type")
        parser.add_argument("-r", "--preserve-aspect-ratio", action=argparse.BooleanOptionalAction,
                            help="preserve the pixel aspect ratio of the input tensor")
        parser.add_argument("--labels", type=str,
                            help="Path to the labels file")
        parser.add_argument("--print-self.intrinsics", action="store_true",
                            help="Print JSON network_intrinsics then exit")
        return parser.parse_args()


if __name__ == "__main__":
    mycam = Vision()
    
    # while True:
    print(mycam.scan())

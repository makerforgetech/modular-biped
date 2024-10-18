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
        Detection.calculate_detection_distances(self, 640, 480)

    @staticmethod
    def calculate_detection_distances(detection, screen_center_x, screen_center_y):
        """Calculate and store the X and Y distances for a detection."""
        # Extract the bounding box values (x, y, width, height)
        x, y, w, h = detection.box

        # Calculate the center of the detection box
        detection_center_x = x + w // 2
        detection_center_y = y + h // 2

        # Calculate the distances between detection center and screen center
        distance_x = abs(detection_center_x - screen_center_x)
        distance_y = abs(detection_center_y - screen_center_y)

        # Store distances in the detection object
        detection.distance_x = distance_x
        detection.distance_y = distance_y
        
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
        
        
        
class PiCamImx500:
    def __init__(self, **kwargs):
        self.last_detections = []
        self.last_results = []
        
        self.args = PiCamImx500.get_args()

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
        self.picam2.start(config, show_preview=False)

        if self.intrinsics.preserve_aspect_ratio:
            self.imx500.set_auto_aspect_ratio()

        self.picam2.pre_callback = self.draw_detections_with_distance
        
        pub.subscribe(self.scan, 'vision:detect')

    def scan(self, captures=1):
        json_array = []
        for i in range(captures):
            self.last_results = self.parse_detections(self.picam2.capture_metadata())
            for i in self.last_results:
                this_capture = [obj.json_out() for obj in self.last_results]
                if captures > 1:
                    json_array = json_array + [this_capture]
                else:
                    json_array = this_capture

        pub.sendMessage('vision:detections', matches=json_array)
        return json_array

    def parse_detections(self, metadata: dict):
        """Parse the output tensor into a number of detected objects, scaled to the ISP out."""
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

    @lru_cache
    def get_labels(self):
        labels = self.intrinsics.labels

        if self.intrinsics.ignore_dash_labels:
            labels = [label for label in labels if label and label != "-"]
        return labels

    # def draw_detections(self, request, stream="main"):
    #     """Draw the detections for this request onto the ISP output."""
    #     detections = self.last_results
    #     if detections is None:
    #         return
    #     labels = self.get_labels()
    #     with MappedArray(request, stream) as m:
    #         for detection in detections:
    #             x, y, w, h = detection.box
    #             label = f"{labels[int(detection.category)]} ({detection.conf:.2f})"

    #             # Calculate text size and position
    #             (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    #             text_x = x + 5
    #             text_y = y + 15

    #             # Create a copy of the array to draw the background with opacity
    #             overlay = m.array.copy()

    #             # Draw the background rectangle on the overlay
    #             cv2.rectangle(overlay,
    #                         (text_x, text_y - text_height),
    #                         (text_x + text_width, text_y + baseline),
    #                         (255, 255, 255),  # Background color (white)
    #                         cv2.FILLED)

    #             alpha = 0.30
    #             cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)

    #             # Draw text on top of the background
    #             cv2.putText(m.array, label, (text_x, text_y),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    #             # Draw detection box
    #             cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)
                
    #         if self.intrinsics.preserve_aspect_ratio:
    #             b_x, b_y, b_w, b_h = self.imx500.get_roi_scaled(request)
    #             color = (255, 0, 0)  # red
    #             cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    #             cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))

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
                distance_label_x = f"X-Dist: {int(distance_x)} px"
                distance_label_y = f"Y-Dist: {int(distance_y)} px"

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
    mycam = PiCamImx500()
    
    # while True:
    print(mycam.scan(1))

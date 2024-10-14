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
    def __init__(self, coords, category, conf, metadata):
        """Create a Detection object, recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)
    def display(self):
        label = f"{PiCamImx500.get_labels()[int(self.category)]} ({self.conf:.2f}%): {self.box}"
        print(label)
        print("")
    def json_out(self):
        return {
            'category': PiCamImx500.get_labels()[int(self.category)],
            'confidence': self.conf,
            'box': self.box
        }
        
        
        
class PiCamImx500:
    def __init__(self, **kwargs):
        self.last_detections = []
        # self.translator = kwargs.get('translator', None)
        # self.service = kwargs.get('service', 'pyttsx3')
        # if self.service == 'elevenlabs':
        #     self.init_elevenlabs(kwargs.get('voice_id', ''))
        # else:
        #     self.init_pyttsx3()
        # # Set subscribers
        # pub.subscribe(self.speak, 'tts')

    # def speak(self, msg):
        # if self.service == 'elevenlabs':
        #     self.speak_elevenlabs(msg)
        # else:
        #     self.speak_pyttsx3(msg)#
        # 
    
    def detect(self, captures):
        # This must be called before instantiation of Picamera2
        imx500 = IMX500(args.model)
        intrinsics = imx500.network_intrinsics
        if not intrinsics:
            intrinsics = NetworkIntrinsics()
            intrinsics.task = "object detection"
        elif intrinsics.task != "object detection":
            print("Network is not an object detection task", file=sys.stderr)
            exit()

        # Override intrinsics from args
        for key, value in vars(args).items():
            if key == 'labels' and value is not None:
                with open(value, 'r') as f:
                    intrinsics.labels = f.read().splitlines()
            elif hasattr(intrinsics, key) and value is not None:
                setattr(intrinsics, key, value)

        # Defaults
        if intrinsics.labels is None:
            with open("assets/coco_labels.txt", "r") as f:
                intrinsics.labels = f.read().splitlines()
        intrinsics.update_with_defaults()

        if args.print_intrinsics:
            print(intrinsics)
            exit()

        picam2 = Picamera2(imx500.camera_num)
        config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12, transform=Transform(vflip=True, hflip=True))

        imx500.show_network_fw_progress_bar()
        picam2.start(config, show_preview=False)

        if intrinsics.preserve_aspect_ratio:
            imx500.set_auto_aspect_ratio()

        last_results = None
        mycam = PiCamImx500()
        picam2.pre_callback = PiCamImx500.draw_detections
        
        json_array = []
        for i in range(captures):
            last_results = mycam.parse_detections(picam2.capture_metadata())
            for i in last_results:
                this_capture = [obj.json_out() for obj in last_results]
                json_array.push(this_capture)
        return json_array

    def parse_detections(self, metadata: dict):
        """Parse the output tensor into a number of detected objects, scaled to the ISP out."""
        bbox_normalization = intrinsics.bbox_normalization
        threshold = args.threshold
        iou = args.iou
        max_detections = args.max_detections

        np_outputs = imx500.get_outputs(metadata, add_batch=True)
        input_w, input_h = imx500.get_input_size()
        if np_outputs is None:
            return self.last_detections
        if intrinsics.postprocess == "nanodet":
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
            Detection(box, category, score, metadata)
            for box, score, category in zip(boxes, scores, classes)
            if score > threshold
        ]
        return self.last_detections

    @staticmethod
    @lru_cache
    def get_labels():
        labels = intrinsics.labels

        if intrinsics.ignore_dash_labels:
            labels = [label for label in labels if label and label != "-"]
        return labels


    @staticmethod
    def draw_detections(request, stream="main"):
        """Draw the detections for this request onto the ISP output."""
        detections = last_results
        if detections is None:
            return
        labels = PiCamImx500.get_labels()
        with MappedArray(request, stream) as m:
            for detection in detections:
                x, y, w, h = detection.box
                label = f"{labels[int(detection.category)]} ({detection.conf:.2f})"

                # Calculate text size and position
                (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                text_x = x + 5
                text_y = y + 15

                # Create a copy of the array to draw the background with opacity
                overlay = m.array.copy()

                # Draw the background rectangle on the overlay
                cv2.rectangle(overlay,
                            (text_x, text_y - text_height),
                            (text_x + text_width, text_y + baseline),
                            (255, 255, 255),  # Background color (white)
                            cv2.FILLED)

                alpha = 0.30
                cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)

                # Draw text on top of the background
                cv2.putText(m.array, label, (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                # Draw detection box
                cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)

            if intrinsics.preserve_aspect_ratio:
                b_x, b_y, b_w, b_h = imx500.get_roi_scaled(request)
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
        parser.add_argument("--print-intrinsics", action="store_true",
                            help="Print JSON network_intrinsics then exit")
        return parser.parse_args()


if __name__ == "__main__":
    mycam = PiCamImx500()
    args = PiCamImx500.get_args()

    # This must be called before instantiation of Picamera2
    imx500 = IMX500(args.model)
    intrinsics = imx500.network_intrinsics
    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
    elif intrinsics.task != "object detection":
        print("Network is not an object detection task", file=sys.stderr)
        exit()

    # Override intrinsics from args
    for key, value in vars(args).items():
        if key == 'labels' and value is not None:
            with open(value, 'r') as f:
                intrinsics.labels = f.read().splitlines()
        elif hasattr(intrinsics, key) and value is not None:
            setattr(intrinsics, key, value)

    # Defaults
    if intrinsics.labels is None:
        with open("assets/coco_labels.txt", "r") as f:
            intrinsics.labels = f.read().splitlines()
    intrinsics.update_with_defaults()

    if args.print_intrinsics:
        print(intrinsics)
        exit()

    picam2 = Picamera2(imx500.camera_num)
    config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12, transform=Transform(vflip=False, hflip=False))

    imx500.show_network_fw_progress_bar()
    picam2.start(config, show_preview=False)

    if intrinsics.preserve_aspect_ratio:
        imx500.set_auto_aspect_ratio()

    last_results = None
    
    picam2.pre_callback = PiCamImx500.draw_detections
    while True:
        
        last_results = mycam.parse_detections(picam2.capture_metadata())
        for i in last_results:
            json_array = [obj.json_out() for obj in last_results]
            print(json_array)

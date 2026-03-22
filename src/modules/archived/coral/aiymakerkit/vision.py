# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Various APIs to simplify inferencing with vision ML models and a camera.

Each class makes it easy to initialize a TensorFlow Lite interpreter for
a certain vision task (such as pose detection or image classification),
and then perform inferencing with an image and get the results in a structure
that's appropriate for that task.

The ``get_frames()`` function makes it easy to get a continuous stream of images
from your camera, and various "draw" functions allow you to overlay your
inference results on the image (such as ``draw_pose()`` to draw a human pose).

For more info, see https://aiyprojects.withgoogle.com/maker/#reference
"""

import os.path
import enum
import platform
import sys

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.adapters import detect
from pycoral.utils import edgetpu

_EDGETPU_SHARED_LIB = {
    'Linux': 'libedgetpu.so.1',
    'Darwin': 'libedgetpu.1.dylib',
    'Windows': 'edgetpu.dll'
}[platform.system()]

VIDEO_SIZE = (640, 480)
CORAL_COLOR = (86, 104, 237)
BLUE = (255, 0, 0)  # BGR (not RGB)


#########################
### VISION MODEL APIS ###
#########################

class KeypointType(enum.IntEnum):
    """Pose keypoints in COCO-style format."""
    NOSE = 0
    LEFT_EYE = 1
    RIGHT_EYE = 2
    LEFT_EAR = 3
    RIGHT_EAR = 4
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_ELBOW = 7
    RIGHT_ELBOW = 8
    LEFT_WRIST = 9
    RIGHT_WRIST = 10
    LEFT_HIP = 11
    RIGHT_HIP = 12
    LEFT_KNEE = 13
    RIGHT_KNEE = 14
    LEFT_ANKLE = 15
    RIGHT_ANKLE = 16


KEYPOINT_EDGES = (
    (KeypointType.NOSE, KeypointType.LEFT_EYE),
    (KeypointType.NOSE, KeypointType.RIGHT_EYE),
    (KeypointType.NOSE, KeypointType.LEFT_EAR),
    (KeypointType.NOSE, KeypointType.RIGHT_EAR),
    (KeypointType.LEFT_EAR, KeypointType.LEFT_EYE),
    (KeypointType.RIGHT_EAR, KeypointType.RIGHT_EYE),
    (KeypointType.LEFT_EYE, KeypointType.RIGHT_EYE),
    (KeypointType.LEFT_SHOULDER, KeypointType.RIGHT_SHOULDER),
    (KeypointType.LEFT_SHOULDER, KeypointType.LEFT_ELBOW),
    (KeypointType.LEFT_SHOULDER, KeypointType.LEFT_HIP),
    (KeypointType.RIGHT_SHOULDER, KeypointType.RIGHT_ELBOW),
    (KeypointType.RIGHT_SHOULDER, KeypointType.RIGHT_HIP),
    (KeypointType.LEFT_ELBOW, KeypointType.LEFT_WRIST),
    (KeypointType.RIGHT_ELBOW, KeypointType.RIGHT_WRIST),
    (KeypointType.LEFT_HIP, KeypointType.RIGHT_HIP),
    (KeypointType.LEFT_HIP, KeypointType.LEFT_KNEE),
    (KeypointType.RIGHT_HIP, KeypointType.RIGHT_KNEE),
    (KeypointType.LEFT_KNEE, KeypointType.LEFT_ANKLE),
    (KeypointType.RIGHT_KNEE, KeypointType.RIGHT_ANKLE),
)


class PoseDetector:
    """Performs inferencing with a pose detection model such as MoveNet.

    Args:
      model (str): Path to a ``.tflite`` file (compiled for the Edge TPU).
    """

    def __init__(self, model):
        self.interpreter = edgetpu.make_interpreter(model)
        self.interpreter.allocate_tensors()

    def get_pose(self, frame):
        """
        Gets the keypoint pose data for one person.

        Args:
          frame: The bitmap image to pass through the model.

        Returns:
          The COCO-style keypoint results, reshaped to [17, 3], in which each
          keypoint has [y, x, score].
        """
        resized_img = cv2.resize(frame, common.input_size(self.interpreter),
                                 fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
        common.set_input(self.interpreter, resized_img)
        self.interpreter.invoke()
        return common.output_tensor(self.interpreter, 0).copy().reshape(
            len(KeypointType), 3)


class PoseClassifier:
    """Performs pose classification with a model from
    `g.co/coral/train-poses <https://g.co/coral/train-poses>`_.

    Args:
      model (str): Path to a ``.tflite`` file.
    """

    def __init__(self, model):
        self.interpreter = tflite.Interpreter(model_path=model)
        self.interpreter.allocate_tensors()

    def get_class(self, keypoints, threshold=0.01):
        """
        Gets the top pose classification result.

        Args:
          keypoints: The COCO-style pose keypoints, as output from a pose
            detection model.
          threshold (float): The minimum confidence score for the returned
            classification.

        Returns:
          The class id for the top result.
        """
        # Reshape input for classify model
        keypoints = keypoints.flatten().reshape(1, 51)
        input_index = self.interpreter.get_input_details()[0]["index"]
        output_index = self.interpreter.get_output_details()[0]["index"]
        self.interpreter.set_tensor(input_index, keypoints)
        self.interpreter.invoke()
        output = self.interpreter.tensor(output_index)
        return np.argmax(output()[0])


def get_keypoint_types(frame, keypoints, threshold=0.01):
    """Converts keypoint data into dictionary with values scaled for the image
    size.

    Args:
      frame: The original image used for pose detection.
      keypoints: A COCO-style keypoints tensor in shape [17, 3], such as
        returned by :func:`PoseDetector.get_pose()`.
      threshold (float): The minimum confidence score for returned results.

    Returns:
      A dictionary with an item for every body keypoint detected above the given
      threshold, wherein each key is the :obj:`KeypointType` and the value is a
      tuple for its (x,y) location.
    """
    height, width, _ = frame.shape
    points = {}
    for i in range(len(KeypointType)):
        score = keypoints[i][2]
        if score > threshold:
            y = int(keypoints[i][0] * height)
            x = int(keypoints[i][1] * width)
            points[i] = (x, y)
    return points


class Detector:
    """Performs inferencing with an object detection model.

    Args:
      model (str): Path to a ``.tflite`` file (compiled for the Edge TPU).
        Must be an SSD model.
    """

    def __init__(self, model):
        self.interpreter = edgetpu.make_interpreter(model)
        self.interpreter.allocate_tensors()

    def get_objects(self, frame, threshold=0.01):
        """
        Gets a list of objects detected in the given image frame.

        Args:
          frame: The bitmap image to pass through the model.
          threshold (float): The minimum confidence score for returned results.

        Returns:
          A list of |Object|_ objects, each of which contains a detected
          object's id, score, and bounding box as |BBox|_.
        """
        height, width, _ = frame.shape
        _, scale = common.set_resized_input(self.interpreter, (width, height),
                                            lambda size: cv2.resize(frame, size,
                                                                    fx=0, fy=0,
                                                                    interpolation=cv2.INTER_CUBIC))
        self.interpreter.invoke()
        return detect.get_objects(self.interpreter, threshold, scale)


class Classifier:
    """Performs inferencing with an image classification model.

    Args:
      model (str): Path to a ``.tflite`` file (compiled for the Edge TPU).
    """

    def __init__(self, model):
        self.interpreter = edgetpu.make_interpreter(model)
        self.interpreter.allocate_tensors()

    def get_classes(self, frame, top_k=1, threshold=0.0):
        """
        Gets classification results as a list of ordered classes.

        Args:
          frame: The bitmap image to pass through the model.
          top_k (int): The number of top results to return.
          threshold (float): The minimum confidence score for returned results.

        Returns:
          A list of |Class|_ objects representing the classification results,
          ordered by scores.
        """
        size = common.input_size(self.interpreter)
        common.set_input(self.interpreter, cv2.resize(frame, size, fx=0, fy=0,
                                                      interpolation=cv2.INTER_CUBIC))
        self.interpreter.invoke()
        return classify.get_classes(self.interpreter, top_k, threshold)


#############################
### CAMERA & DISPLAY APIS ###
#############################

def draw_classes(frame, classes, labels, color=CORAL_COLOR):
    """
    Draws image classification names on the display image.

    Args:
      frame: The bitmap image to draw upon.
      classes: A list of |Class|_  objects representing the classified objects.
      labels (str): The labels file corresponding to model used for image
        classification.
      color (tuple): The BGR color (int,int,int) to use for the text.
    """
    for index, score in classes:
        label = '%s (%.2f)' % (labels.get(index, 'n/a'), score)
        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_PLAIN, 2.0, color,
                    2)


def draw_objects(frame, objs, labels=None, color=CORAL_COLOR, thickness=5):
    """
    Draws bounding boxes for detected objects on the display image.

    Args:
      frame: The bitmap image to draw upon.
      objs: A list of |Object|_ objects for which you want to draw bounding
        boxes on the frame.
      labels (str): The labels file corresponding to the model used for object
        detection.
      color (tuple): The BGR color (int,int,int) to use for the bounding box.
      thickness (int): The bounding box pixel thickness.
    """
    for obj in objs:
        bbox = obj.bbox
        cv2.rectangle(frame, (bbox.xmin, bbox.ymin), (bbox.xmax, bbox.ymax),
                      color, thickness)
        if labels:
            cv2.putText(frame, labels.get(obj.id),
                        (bbox.xmin + thickness, bbox.ymax - thickness),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                        color=CORAL_COLOR, thickness=2)


def draw_pose(frame, keypoints, threshold=0.2, color=CORAL_COLOR,
              circle_radius=5, line_thickness=2):
    """Draws the pose skeleton on the image sent to the display and returns
    structured keypoints.

    Args:
      frame: The bitmap image to draw upon.
      keypoints: A COCO-style pose keypoints tensor in shape [17, 3], such as
        returned by :func:`PoseDetector.get_pose()`.
      threshold (float): The minimum confidence score for returned keypoint data.
      color (tuple): The BGR color (int,int,int) to use for the bounding box.
      circle_radius (int): The radius size of each keypoint dot.
      line_thickness (int): The pixel thickness for lines connecting the
        keypoint dots.

    Returns:
      A dictionary with an item for every body keypoint that is detected above
      the given threshold, wherein each key is the :obj:`KeypointType` and the
      value is at tuple for its (x,y) location.
      (Exactly the same return as :func:`get_keypoint_types()`.)
    """
    # Get the structured keypoint types
    points = get_keypoint_types(frame, keypoints, threshold)
    # Draw all points (that have scores greater than the threshold)
    for point in points.values():
        cv2.circle(frame, point, radius=circle_radius, color=color,
                   thickness=-1)
    # Draw lines between points if both point pairs are found
    for a, b in KEYPOINT_EDGES:
        if a in points and b in points:
            cv2.line(frame, points[a], points[b], color,
                     thickness=line_thickness)
    return points


def draw_label(frame, label, color=CORAL_COLOR):
    """
    Draws a text label on the image sent to the display.

    Args:
      frame: The bitmap image to draw upon.
      label (str): The string to write.
      color (tuple): The BGR color (int,int,int) for the text.
    """
    cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_PLAIN, 2.0, color, 2)


def draw_circle(frame, point, radius, color=CORAL_COLOR, thickness=5):
    """Draws a circle onto the image sent to the display.

    Args:
      frame: The bitmap image to draw upon.
      point (tuple): An (x,y) tuple specifying the circle center.
      radius (int): The radius size of the circle.
      color (tuple): The BGR color (int,int,int) to use.
      thickness (int): The circle's pixel thickness. Set to -1 to fill the
        circle.
    """
    cv2.circle(frame, point, radius, color, thickness)


def draw_rect(frame, bbox, color=BLUE, thickness=5):
    """Draws a rectangle onto the image sent to the display.

    Args:
      frame: The bitmap image to draw upon.
      bbox: A |BBox|_  object.
      color (tuple): The BGR color (int,int,int) to use.
      thickness (int): The box pixel thickness. Set to -1 to fill the box."""
    cv2.rectangle(frame, (bbox.xmin, bbox.ymin), (bbox.xmax, bbox.ymax), color,
                  thickness)


def get_frames(title='Camera', size=VIDEO_SIZE, handle_key=None,
               capture_device_index=0, mirror=True, display=True,
               return_key=False):
    """
    Gets a stream of image frames from the camera.

    Args:
      title (str): A title for the display window.
      size (tuple): The image resolution for all frames, as an int tuple (x,y).
      handle_key: A callback function that accepts arguments (key, frame) for
        a key event and the image frame from the moment the key was pressed.
        This has no effect if display is False.
      capture_device_index (int): The Linux device ID for the camera.
      mirror (bool): Whether to flip the images horizontally (set True for a
        selfie view).
      display (bool): Whether to show the camera images in a desktop window
        (set False if you don't use a desktop).
      return_key (bool): Whether to also return any key presses. If True, the
        function returns a tuple with (frame, key) instead of just the frame.

    Returns:
      An iterator that yields each image frame from the default camera. Or a
      tuple if ``return_key`` is True.
    """
    width, height = size

    if display and not handle_key:
        print("Press Q to quit")

        def handle_key(key, frame):
            if key == ord('q') or key == ord('Q'):
                return False
            return True

    attempts = 5
    while True:
        cap = cv2.VideoCapture(capture_device_index)
        success, _ = cap.read()
        if success:
            print("Camera started successfully.")
            break

        if attempts == 0:
            print(
                "Cannot initialize camera!\nMake sure the camera is connected.",
                file=sys.stderr)
            sys.exit(1)

        cap.release()
        attempts -= 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    try:
        while True:
            key = cv2.waitKey(1)
            success, frame = cap.read()
            if mirror:
                frame = cv2.flip(frame, 1)
            if success:
                if return_key:
                    yield (frame, key)
                else:
                    yield frame
                if display:
                    cv2.imshow(title, frame)

            if key != -1 and not handle_key(key, frame):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def save_frame(filename, frame):
    """
    Saves an image to a specified location.

    Args:
      filename (str): The path where you'd like to save the image.
      frame: The bitmap image to save.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    cv2.imwrite(filename, frame)

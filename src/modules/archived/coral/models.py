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
A collection of TensorFlow Lite models for use with aiymakerkit examples.

These files are already downloaded if you flashed the AIY Maker Kit
system image for Raspberry Pi. Otherwise, you must download them by
running the download_models.sh script in this directory.
"""

import os.path

def path(name):
    root = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(root, 'models', name)

# Models
FACE_DETECTION_MODEL = path('ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite')
OBJECT_DETECTION_MODEL = path('ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite')
CLASSIFICATION_MODEL = path('tf2_mobilenet_v2_1.0_224_ptq_edgetpu.tflite')
CLASSIFICATION_IMPRINTING_MODEL = path('mobilenet_v1_1.0_224_l2norm_quant_edgetpu.tflite')
MOVENET_MODEL = path('movenet_single_pose_lightning_ptq_edgetpu.tflite')

# Labels
CLASSIFICATION_LABELS = path('imagenet_labels.txt')
OBJECT_DETECTION_LABELS = path('coco_labels.txt')

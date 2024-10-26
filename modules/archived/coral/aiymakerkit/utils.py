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
Utility functions for use with the vision and audio modules.
"""

import json

from tflite_support import metadata


def _associcated_labels_file(metadata_json):
    for ot in metadata_json['subgraph_metadata'][0]['output_tensor_metadata']:
      if 'associated_files' in ot:
        for af in ot['associated_files']:
          if af['type'] in ('TENSOR_AXIS_LABELS', 'TENSOR_VALUE_LABELS'):
            return af['name']
    raise ValueError('Model metadata does not have associated labels file')


def read_labels_from_metadata(model):
    """Read labels from the model file metadata.

    Args:
        model (str): Path to the ``.tflite`` file.
    Returns:
        A dictionary of (int, string), mapping label ids to text labels.
    """
    displayer = metadata.MetadataDisplayer.with_model_file(model)
    metadata_json = json.loads(displayer.get_metadata_json())
    labels_file = _associcated_labels_file(metadata_json)
    labels = displayer.get_associated_file_buffer(labels_file).decode()
    return {i: label for i, label in enumerate(labels.splitlines())}

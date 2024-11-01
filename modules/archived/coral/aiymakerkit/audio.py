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
APIs to simplify audio classification with a microphone.

For more info, see https://aiyprojects.withgoogle.com/maker/#reference
"""

import contextlib
import json
import numpy as np
import os
import queue
import sys
import threading

import pyaudio
import tflite_runtime.interpreter as tflite

from pycoral.utils import dataset
from tflite_support import metadata

from . import ring_buffer
from . import utils


@contextlib.contextmanager
def pyaudio_stream(*args, **kwargs):
    """Context manager for the PyAudio stream."""
    audio = pyaudio.PyAudio()
    try:
        stream = audio.open(*args, **kwargs)
        try:
            yield stream
        finally:
            stream.stop_stream()
            stream.close()
    finally:
        audio.terminate()


def model_audio_properties(model_file):
    """
    Returns the audio sample rate and number of channels that must be used with
    the given model (as a tuple in that order).
    """
    displayer = metadata.MetadataDisplayer.with_model_file(model_file)
    metadata_json = json.loads(displayer.get_metadata_json())
    if metadata_json['name'] != 'AudioClassifier':
        raise ValueError('Model must be an audio classifier')
    props = metadata_json['subgraph_metadata'][0]['input_tensor_metadata'][0]['content']['content_properties']
    return int(props['sample_rate']), int(props['channels'])


def classify_audio(model, callback,
                   labels_file=None,
                   inference_overlap_ratio=0.1,
                   buffer_size_secs=2.0,
                   buffer_write_size_secs=0.1,
                   audio_device_index=None):
    """
    Continuously classifies audio samples from the microphone, yielding results
    to your own callback function.

    Your callback function receives the top classification result for every
    inference performed. Although the audio sample size is fixed based on the
    model input size, you can adjust the rate of inference with
    ``inference_overlap_ratio``. A larger overlap means the model runs inference
    more frequently but with larger amounts of sample data shared between
    inferences, which can result in duplicate results.

    Args:
        model (str): Path to a ``.tflite`` file.
        callback: A function that takes two arguments (in order): a string for
            the classification label, and a float for the prediction score.
            The function must return a boolean: True to continue running
            inference, or False to stop.
        labels_file (str): Path to a labels file (required only if the model
            does not include metadata labels). If provided, this overrides the
            labels file provided in the model metadata.
        inference_overlap_ratio (float): The amount of audio that should overlap
            between each sample used for inference. May be 0.0 up to (but not
            including) 1.0. For example, if set to 0.5 and the model takes a
            one-second sample as input, the model will run an inference every
            half second, or if set to 0, then there is no overlap and
            it will run once each second.
        buffer_size_secs (float): The length of audio to hold in the audio
            buffer.
        buffer_write_size_secs (float): The length of audio to capture into the
            buffer with each sampling from the microphone.
        audio_device_index (int): The audio input device index to use.
    """
    if not model:
        raise ValueError('model must be specified')

    if buffer_size_secs <= 0.0:
        raise ValueError('buffer_size_secs must be positive')

    if buffer_write_size_secs <= 0.0:
        raise ValueError('buffer_write_size_secs must be positive')

    if inference_overlap_ratio < 0.0 or \
       inference_overlap_ratio >= 1.0:
        raise ValueError('inference_overlap_ratio must be in [0.0 .. 1.0)')

    sample_rate_hz, channels = model_audio_properties(model)

    if labels_file is not None:
        labels = dataset.read_label_file(labels_file)
    else:
        labels = utils.read_labels_from_metadata(model)

    print('Say one of the following:')
    for value in labels.values():
        print('  %s' % value)

    interpreter = tflite.Interpreter(model_path=model)
    interpreter.allocate_tensors()

    # Input tensor
    input_details = interpreter.get_input_details()
    waveform_input_index = input_details[0]['index']
    _, num_audio_frames = input_details[0]['shape']
    waveform = np.zeros(num_audio_frames, dtype=np.float32)

    # Output tensor
    output_details = interpreter.get_output_details()
    scores_output_index = output_details[0]['index']

    ring_buffer_size = int(buffer_size_secs * sample_rate_hz)
    frames_per_buffer = int(buffer_write_size_secs * sample_rate_hz)
    remove_size = int((1.0 - inference_overlap_ratio) * len(waveform))

    rb = ring_buffer.ConcurrentRingBuffer(
        np.zeros(ring_buffer_size, dtype=np.float32))

    def stream_callback(in_data, frame_count, time_info, status):
        try:
            rb.write(np.frombuffer(in_data, dtype=np.float32), block=False)
        except ring_buffer.Overflow:
            print('WARNING: Dropping input audio buffer', file=sys.stderr)

        return None, pyaudio.paContinue

    with pyaudio_stream(format=pyaudio.paFloat32,
                        channels=channels,
                        rate=sample_rate_hz,
                        frames_per_buffer=frames_per_buffer,
                        stream_callback=stream_callback,
                        input=True,
                        input_device_index=audio_device_index) as stream:
        keep_listening = True
        while keep_listening:
            rb.read(waveform, remove_size=remove_size)

            interpreter.set_tensor(waveform_input_index, [waveform])
            interpreter.invoke()
            scores = interpreter.get_tensor(scores_output_index)
            scores = np.mean(scores, axis=0)
            prediction = np.argmax(scores)
            keep_listening = callback(labels[prediction], scores[prediction])


class AudioClassifier:
    """Performs classifications with a speech classification model.

    This is intended for situations where you want to write a loop in your code
    that fetches new classification results in each iteration (by calling
    :func:`next()`). If you instead want to receive a callback each time a new
    classification is detected, instead use :func:`classify_audio()`.

    Args:
        model (str): Path to a ``.tflite`` file.
        labels_file (str): Path to a labels file (required only if the model
            does not include metadata labels). If provided, this overrides the
            labels file provided in the model metadata.
        inference_overlap_ratio (float): The amount of audio that should overlap
            between each sample used for inference. May be 0.0 up to (but not
            including) 1.0. For example, if set to 0.5 and the model takes a
            one-second sample as input, the model will run an inference every
            half second, or if set to 0, it will run once each second.
        buffer_size_secs (float): The length of audio to hold in the audio
            buffer.
        buffer_write_size_secs (float): The length of audio to capture into the
            buffer with each sampling from the microphone.
        audio_device_index (int): The audio input device index to use.
    """

    def __init__(self, **kwargs):
        self._queue = queue.Queue()
        self._thread = threading.Thread(
            target=classify_audio,
            kwargs={'callback': self._callback, **kwargs},
            daemon=True)
        self._thread.start()

    def _callback(self, label, score):
        self._queue.put((label, score))
        return True

    def next(self, block=True):
        """
        Returns a single speech classification.

        Each time you call this, it pulls from a queue of recent
        classifications. So even if there are many classifications in a short
        period of time, this always returns them in the order received.

        Args:
            block (bool): Whether this function should block until the next
                classification arrives (if there are no queued classifications).
                If False, it always returns immediately and returns None if the
                classification queue is empty.
        """
        try:
            result = self._queue.get(block)
            self._queue.task_done()
            return result
        except queue.Empty:
            return None

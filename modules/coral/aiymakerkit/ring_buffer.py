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
Back-end APIs used by the audio module to handle the microphone stream.

Not intended for use in applications.
"""

import threading


class Overflow(Exception):
    """Exception raised when ring buffer does not have enough space to write."""
    pass


class Underflow(Exception):
    """Exception raised when ring buffer does not have enough data to read."""
    pass


class RingBuffer:
    """Simple ring buffer implementation.

    https://en.wikipedia.org/wiki/Circular_buffer
    """

    def __init__(self, buf):
        self._buf = buf
        self._r = 0
        self._size = 0

    def __len__(self):
        return len(self._buf)

    def __str__(self):
        return str(self._buf)

    @property
    def read_size(self):
        return self._size

    @property
    def write_size(self):
        return len(self) - self.read_size

    def read_only(self, buf):
        size = len(buf)

        if size == 0:
            return

        if size > self.read_size:
            raise Underflow

        f = self._r
        l = (f + size) % len(self)

        if f < l:
            buf[:] = self._buf[f:l]
        else:
            n = len(self) - f
            buf[:n] = self._buf[f:]
            buf[n:] = self._buf[:l]

    def remove_only(self, size):
        if size < 0:
            raise ValueError("'size' must be a non-negative number")

        if size > self.read_size:
            raise Underflow

        self._r = (self._r + size) % len(self)
        self._size -= size

    def read(self, buf):
        self.read_only(buf)
        self.remove_only(len(buf))

    def write(self, buf):
        size = len(buf)

        if size == 0:
            return

        if size > self.write_size:
            raise Overflow

        f = (self._r + self._size) % len(self)
        l = (f + size) % len(self)

        if f < l:
            self._buf[f:l] = buf
        else:
            n = len(self) - f
            self._buf[f:] = buf[:n]
            self._buf[:l] = buf[n:]

        self._size += size


class ConcurrentRingBuffer:
    """Blocking ring buffer for concurrent access from multiple threads."""

    def __init__(self, buf):
        self._rb = RingBuffer(buf)
        self._lock = threading.Lock()
        self._overflow = threading.Condition(self._lock)
        self._underflow = threading.Condition(self._lock)

    def __str__(self):
        return str(self._rb)

    def write(self, buf, block=True, timeout=None):
        if len(buf) > len(self._rb):
            raise ValueError("'buf' is too big")

        with self._lock:
            if block and not self._overflow.wait_for(
                    lambda: len(buf) <= self._rb.write_size, timeout):
                raise Overflow

            self._rb.write(buf)
            self._underflow.notify()

    def read(self, buf, remove_size=None, block=True, timeout=None):
        if len(buf) > len(self._rb):
            raise ValueError("'buf' is too big")

        if remove_size is not None:
            if remove_size < 0:
                raise ValueError("'remove_size' must be non-negative")
            if remove_size > len(buf):
                raise ValueError("'remove_size' must not exceed 'len(buf)'")

        with self._lock:
            if block and not self._underflow.wait_for(
                    lambda: len(buf) <= self._rb.read_size, timeout):
                raise Underflow

            self._rb.read_only(buf)
            self._rb.remove_only(
                len(buf) if remove_size is None else remove_size)
            self._overflow.notify()

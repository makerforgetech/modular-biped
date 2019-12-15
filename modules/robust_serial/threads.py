from __future__ import print_function, division, absolute_import

import threading
import time

import serial

from .robust_serial import write_order, Order, write_i8, write_i16, decode_order
from .utils import queue

rate = 1 / 2000  # 2000 Hz (limit the rate of communication with the arduino)


class CommandThread(threading.Thread):
    """
    Thread that send orders to the arduino
    it blocks if there no more send_token left (here it is the n_received_semaphore).

    :param serial_file: (Serial object)
    :param command_queue: (Queue)
    :param exit_event: (Threading.Event object)
    :param n_received_semaphore: (threading.Semaphore)
    :param serial_lock: (threading.Lock)
    """

    def __init__(self, serial_file, command_queue, exit_event, n_received_semaphore, serial_lock):
        threading.Thread.__init__(self)
        self.deamon = True
        self.serial_file = serial_file
        self.command_queue = command_queue
        self.exit_event = exit_event
        self.n_received_semaphore = n_received_semaphore
        self.serial_lock = serial_lock

    def run(self):
        while not self.exit_event.is_set():
            self.n_received_semaphore.acquire()
            if self.exit_event.is_set():
                break
            try:
                order, param = self.command_queue.get_nowait()
            except queue.Empty:
                time.sleep(rate)
                self.n_received_semaphore.release()
                continue

            with self.serial_lock:
                write_order(self.serial_file, order)
                # print("Sent {}".format(order))
                if order == Order.MOTOR:
                    write_i8(self.serial_file, param)
                elif order == Order.SERVO:
                    write_i16(self.serial_file, param)
            time.sleep(rate)
        print("Command Thread Exited")


class ListenerThread(threading.Thread):
    """
    Thread that listen to the Arduino
    It is used to add send_tokens to the n_received_semaphore

    :param serial_file: (Serial object)
    :param exit_event: (threading.Event object)
    :param n_received_semaphore: (threading.Semaphore)
    :param serial_lock: (threading.Lock)
    """

    def __init__(self, serial_file, exit_event, n_received_semaphore, serial_lock):
        threading.Thread.__init__(self)
        self.deamon = True
        self.serial_file = serial_file
        self.exit_event = exit_event
        self.n_received_semaphore = n_received_semaphore
        self.serial_lock = serial_lock

    def run(self):
        while not self.exit_event.is_set():
            try:
                bytes_array = bytearray(self.serial_file.read(1))
            except serial.SerialException:
                time.sleep(rate)
                continue
            if not bytes_array:
                time.sleep(rate)
                continue
            byte = bytes_array[0]
            with self.serial_lock:
                try:
                    order = Order(byte)
                except ValueError:
                    continue
                if order == Order.RECEIVED:
                    self.n_received_semaphore.release()
                decode_order(self.serial_file, byte)
            time.sleep(rate)
        print("Listener Thread Exited")

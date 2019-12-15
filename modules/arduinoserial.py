# MODE ROBUST
from __future__ import print_function, division, absolute_import
import time
from modules.robust_serial.robust_serial import write_order, Order, write_i8, write_i16, read_i8, read_order
from modules.robust_serial.utils import open_serial_port
# MODE_SIMPLE
import serial


class ArduinoSerial:
    """
    Communicate with Arduino over Serial
    """

    MODE_SIMPLE = 0
    MODE_ROBUST = 1

    DEVICE_LED = 0
    DEVICE_SERVO = 1
    DEVICE_PIN = 2

    def __init__(self, robust=False, **kwargs):

        if robust:
            self.mode = ArduinoSerial.MODE_ROBUST
            self.serial_file = ArduinoSerial.initialise()
            self.file = None
        else:
            self.mode = ArduinoSerial.MODE_SIMPLE
            self.arduino = serial.Serial('/dev/ttyACM0', 9600)

    @staticmethod
    def initialise():
        try:
            serial_file = open_serial_port(baudrate=115200, timeout=None)
        except Exception as e:
            raise e

        is_connected = False
        # Initialize communication with Arduino
        while not is_connected:
            print("Waiting for arduino...")
            write_order(serial_file, Order.HELLO)
            bytes_array = bytearray(serial_file.read(1))
            if not bytes_array:
                time.sleep(2)
                continue
            byte = bytes_array[0]
            if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
                is_connected = True

        print("Connected to Arduino")
        return serial_file

    # send(ArduinoSerial.DEVICE_SERVO, 18, 20)
    # send(ArduinoSerial.DEVICE_LED, 1, (20,20,20))
    # send(ArduinoSerial.DEVICE_LED, range(9), (20,20,20))
    def send(self, type, identifier, message):
        if self.mode == ArduinoSerial.MODE_SIMPLE:
            self.arduino.write(message.encode())
            # send(None, None, 20,20,20) # would control all 3 servos
        else:
            if type == ArduinoSerial.DEVICE_SERVO:
                write_order(self.serial_file, Order.SERVO)
                write_i8(self.serial_file, identifier)
                write_i8(self.serial_file, message)
            elif type == ArduinoSerial.DEVICE_LED:
                write_order(self.serial_file, Order.LED)
                if isinstance(identifier, list) or isinstance(identifier, range):
                    # write the number of leds to update
                    write_i8(self.serial_file, len(identifier))
                    for i in identifier:
                        write_i8(self.serial_file, i)
                else:
                    write_i8(self.serial_file, 1)
                    write_i8(self.serial_file, identifier)

                if isinstance(message, tuple):
                    for v in message:
                        write_i8(self.serial_file, v)
                else:
                    write_i16(self.serial_file, message)

            elif type == ArduinoSerial.DEVICE_PIN:
                write_order(self.serial_file, Order.PIN)
                write_i8(self.serial_file, identifier)
                write_i8(self.serial_file, message)


        print(read_order(self.serial_file))

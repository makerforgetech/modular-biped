from __future__ import print_function, division, absolute_import
import time
from modules.robust_serial.robust_serial import write_order, Order, write_i8, write_i16, read_i8, read_i16, read_i32, read_order
from modules.robust_serial.utils import open_serial_port
from pubsub import pub

class ArduinoSerial:
    """
    Communicate with Arduino over Serial
    """
    type_map=['led', 'servo',' pin', 'read']
    DEVICE_LED = 0
    DEVICE_SERVO = 1
    DEVICE_PIN = 2
    DEVICE_PIN_READ = 3

    ORDER_RECEIVED = 5
    def __init__(self, **kwargs):
        self.serial_file = ArduinoSerial.initialise()
        self.file = None
        pub.subscribe(self.send, 'serial')

    @staticmethod
    def initialise():
        try:
            serial_file = open_serial_port(baudrate=115200, timeout=None)
        except Exception as e:
            raise e

        is_connected = False
        # Initialize communication with Arduino
        while not is_connected:
            pub.sendMessage('log', msg="[ArduinoSerial] Waiting for arduino...")
            write_order(serial_file, Order.HELLO)
            bytes_array = bytearray(serial_file.read(1))
            if not bytes_array:
                time.sleep(2)
                continue
            byte = bytes_array[0]
            if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
                is_connected = True

        pub.sendMessage('log', msg="[ArduinoSerial] Connected to Arduino")
        return serial_file

    def send(self, type, identifier, message):
        """
        Examples:
        # send(ArduinoSerial.DEVICE_SERVO, 18, 20)
        # send(ArduinoSerial.DEVICE_LED, 1, (20,20,20))
        # send(ArduinoSerial.DEVICE_LED, range(9), (20,20,20))
        :param type: one of the DEVICE_ types
        :param identifier: an identifier or list / range of identifiers, pin or LED number
        :param message: the packet to send to the arduino
        """
        pub.sendMessage('log', msg='[ArduinoSerial] ' + str(ArduinoSerial.type_map[type]) + ' id: ' + str(identifier) + ' val: ' + str(message))
        if type == ArduinoSerial.DEVICE_SERVO or type == 'servo':
            write_order(self.serial_file, Order.SERVO)
            write_i8(self.serial_file, identifier)
            write_i16(self.serial_file, int(message))
        elif type == ArduinoSerial.DEVICE_LED or type == 'led':
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

        elif type == ArduinoSerial.DEVICE_PIN or type == 'pin':
            write_order(self.serial_file, Order.PIN)
            write_i8(self.serial_file, identifier)
            write_i8(self.serial_file, message)

        elif type == ArduinoSerial.DEVICE_PIN_READ or type == 'pin_read':
            write_order(self.serial_file, Order.READ)
            write_i8(self.serial_file, identifier)
            return read_i16(self.serial_file)

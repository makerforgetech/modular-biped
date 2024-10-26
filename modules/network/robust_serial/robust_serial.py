from __future__ import print_function, division, unicode_literals, absolute_import

import struct

from enum import Enum


class Order(Enum):
    """
    Pre-defined orders
    """

    HELLO = 0
    SERVO = 1
    SERVO_RELATIVE = 2
    ALREADY_CONNECTED = 3
    ERROR = 4
    RECEIVED = 5
    STOP = 6
    LED = 7
    PIN = 8
    READ = 9

def read_order(f):
    """
    :param f: file handler or serial file
    :return: (Order Enum Object)
    """
    return Order(read_i8(f))

def read_i8(f):
    """
    :param f: file handler or serial file
    :return: (int8_t)
    """
    return struct.unpack('<b', bytearray(f.read(1)))[0]


def read_i16(f):
    """
    :param f: file handler or serial file
    :return: (int16_t)
    """
    return struct.unpack('<h', bytearray(f.read(2)))[0]


def read_i32(f):
    """
    :param f: file handler or serial file
    :return: (int32_t)
    """
    return struct.unpack('<l', bytearray(f.read(4)))[0]


def write_i8(f, value):
    """
    :param f: file handler or serial file
    :param value: (int8_t)
    """
    if -128 <= value <= 127:
        f.write(struct.pack('<b', value))
    else:
        print("Value error:{}".format(value))


def write_order(f, order):
    """
    :param f: file handler or serial file
    :param order: (Order Enum Object)
    """
    write_i8(f, order.value)


def write_i16(f, value):
    """
    :param f: file handler or serial file
    :param value: (int16_t)
    """
    f.write(struct.pack('<h', value))


def write_i32(f, value):
    """
    :param f: file handler or serial file
    :param value: (int32_t)
    """
    f.write(struct.pack('<l', value))


def decode_order(f, byte, debug=False):
    """
    :param f: file handler or serial file
    :param byte: (int8_t)
    :param debug: (bool) whether to print or not received messages
    """
    try:
        order = Order(byte)
        if order == Order.HELLO:
            msg = "HELLO"
        elif order == Order.SERVO:
            angle = read_i16(f)
            # Bit representation
            # print('{0:016b}'.format(angle))
            msg = "SERVO {}".format(angle)
        elif order == Order.MOTOR:
            speed = read_i8(f)
            msg = "motor {}".format(speed)
        elif order == Order.ALREADY_CONNECTED:
            msg = "ALREADY_CONNECTED"
        elif order == Order.ERROR:
            error_code = read_i16(f)
            msg = "Error {}".format(error_code)
        elif order == Order.RECEIVED:
            msg = "RECEIVED"
        elif order == Order.STOP:
            msg = "STOP"
        elif order == Order.LED:
            identifier = read_i8(f)
            msg = "led {}".format(identifier)
        else:
            msg = ""
            print("Unknown Order", byte)

        if debug:
            print(msg)
    except Exception as e:
        print("Error decoding order {}: {}".format(byte, e))
        print('byte={0:08b}'.format(byte))

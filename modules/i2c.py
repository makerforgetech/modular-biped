from pubsub import pub
import os
from time import sleep

from adafruit_servokit import ServoKit


class I2C:
    def __init__(self, **kwargs):
        # Scan with `sudo i2cdetect -y 1`
        kit = ServoKit(channels=16)
        # https://learn.adafruit.com/adafruit-16-channel-servo-driver-with-raspberry-pi/using-the-adafruit-library
        print("I2C initialized, moving servo to 180")
        kit.servo[0].angle = 180 # Range 0 to 180
        sleep(1)
        print("moving servo to 90")
        kit.servo[0].angle = 90 # Range 0 to 180
        sleep(1)
        print("moving servo to 0")
        kit.servo[0].angle = 0 # Range 0 to 180
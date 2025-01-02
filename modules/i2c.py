from pubsub import pub
import os
from time import sleep

from adafruit_servokit import ServoKit

class I2C:
    def __init__(self, **kwargs):
        # Scan with `sudo i2cdetect -y 1`
        self.servos = ServoKit(channels=16)
        # https://learn.adafruit.com/adafruit-16-channel-servo-driver-with-raspberry-pi/using-the-adafruit-library
        print("Initiated i2c moving servo to 90")
        self.moveServo(0, 90)
        sleep(1)
    
    def moveServo(self, index, angle):
        self.servos.servo[index].angle = angle
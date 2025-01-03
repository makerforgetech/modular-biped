from pubsub import pub
import os
from time import sleep

from adafruit_servokit import ServoKit

class I2C:
    def __init__(self, **kwargs):
        # Scan with `sudo i2cdetect -y 1`
        self.servos = ServoKit(channels=16)
        self.count = kwargs.get('servo_count')
        # https://learn.adafruit.com/adafruit-16-channel-servo-driver-with-raspberry-pi/using-the-adafruit-library
        for i in range(self.count):
            self.moveServo(i, 90)
        if kwargs.get('test_on_boot'):
            self.test()
    
    def moveServo(self, index, angle):
        self.servos.servo[index].angle = angle
        
    def test(self):
        for i in range(self.count):
            print("Testing servo {}".format(i))
            self.moveServo(i, 0)
            sleep(1)
            self.moveServo(i, 180)
            sleep(1)
            self.moveServo(i, 90)
            sleep(1)
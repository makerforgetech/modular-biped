from adafruit_servokit import ServoKit
from modules.actuators.base_servo.py import BaseServo

class I2CServo(BaseServo):

    def __init__(self, **kwargs):
        """
        I2CServo class
        Uses I2C to control servos via PCA9685 driver board
        
        :param kwargs: pin, name, id, range, power, start_pos, buffer, delta, servo_count, test_on_boot
        """
        super().__init__(**kwargs)
        self.servos = ServoKit(channels=16)
        self.count = kwargs.get('servo_count', 16)  # @todo: change to reference a single servo. Research how to achieve this with ServoKit
        for i in range(self.count):
            self.moveServo(i, 90)
        if kwargs.get('test_on_boot'):
            self.test()

    def perform_move(self, position):
        self.servos.servo[self.index].angle = position

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
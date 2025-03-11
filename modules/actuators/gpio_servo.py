from gpiozero import AngularServo
from modules.actuators.base_servo.py import BaseServo

class GPIOServo(BaseServo):

    def __init__(self, **kwargs):
        """
        GPIOServo class
        Uses GPIO to control servos directly from Raspberry Pi
        
        :param kwargs: pin, name, id, range, power, start_pos, buffer, delta
        """
        super().__init__(**kwargs)
        self.servo = AngularServo(self.pin, min_angle=self.range[0], max_angle=self.range[1], initial_angle=self.start)

    def perform_move(self, position):
        self.servo.angle = position
        sleep(1)
        self.servo.detach()
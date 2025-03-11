from gpiozero import AngularServo
from modules.config import Config
from time import sleep
from modules.base_module import BaseModule

class PiServo(BaseModule):

    def __init__(self, **kwargs):
        """
        PiServo class
        :param kwargs: pin, range, start
        :param pin: GPIO pin number
        :param range: [min, max] angle range
        :param start: initial angle
        
        Install: pip install gpiozero
        
        Subscribes to 'piservo:move' to move servo
        - Argument: angle (int) - angle to move servo
        
        Example:
        self.publish('piservo:move', angle=90)        
        """
        
        self.pin = kwargs.get('pin')
        self.range = kwargs.get('range')
        self.start = kwargs.get('start', 0)
        self.servo = None
        # print(self.range)
        # self.move(0)
        # sleep(2)
        # self.move(self.range[0])
        # sleep(2)
        # self.move(self.range[1])
        # sleep(2)
        self.move(self.start)
        
    def setup_messaging(self):
        self.subscribe('piservo:move', self.move)

    def move(self, angle):
        if self.servo is None:
            self.servo = AngularServo(self.pin, min_angle=self.range[0], max_angle=self.range[1], initial_angle=self.start)
        self.servo.angle = angle                # Changes the angle (to move the servo)
        sleep(1)                                # @TODO: Remove this sleep
        self.servo.detach()                     # Detaches the servo (to stop jitter)
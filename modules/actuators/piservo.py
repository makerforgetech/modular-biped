from gpiozero import AngularServo
from modules.config import Config
from time import sleep
from pubsub import pub

class PiServo:

    def __init__(self, pin, range, **kwargs):
        self.pin = pin
        self.range = range
        self.start = kwargs.get('start_pos', 0)
        self.servo = None
        # print(range)
        pub.subscribe(self.move, 'piservo:move')
        self.move(0)
        sleep(2)
        self.move(range[0])
        sleep(2)
        self.move(range[1])
        sleep(2)
        self.move(self.start)
        

    def move(self, angle):
        if self.servo is None:
            self.servo = AngularServo(self.pin, min_angle=self.range[0], max_angle=self.range[1], initial_angle=self.start)
        self.servo.angle = angle                # Changes the angle (to move the servo)
        sleep(1)                                # @TODO: Remove this sleep
        self.servo.detach()                     # Detaches the servo (to stop jitter)
from gpiozero import AngularServo
from modules.config import Config
from time import sleep
from pubsub import pub

class PiServo:

    def __init__(self, pin, range, **kwargs):
        self.pin = pin
        self.range = range
        self.start = kwargs.get('start_pos', 0)
        print(range)
        self.servo = AngularServo(pin, min_angle=range[0], max_angle=range[1], initial_angle=self.start)
        pub.subscribe(self.move, 'piservo:move')

    def move(self, angle):
        self.servo.angle = angle                # Changes the angle (to move the servo)
        sleep(1)                                # @TODO: Remove this sleep
# Source: https://github.com/stripcode/pigpio-stepper-motor/blob/master/PigpioStepperMotor.py
import pigpio
from time import sleep
from collections import deque

fullStepSequence = (
    (1, 0, 0, 0),
    (0, 1, 0, 0),
    (0, 0, 1, 0),
    (0, 0, 0, 1)
)

halfStepSequence = (
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1)
)

shortSequence = (
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 0, 1, 1),
    (0, 0, 1, 0)
)


class StepperMotor:

    def __init__(self, pins, **kwargs):
        pi = pigpio.pi()  # modified to include pigpio reference directly
        pi.set_mode(pins[0], pigpio.OUTPUT)
        pi.set_mode(pins[1], pigpio.OUTPUT)
        pi.set_mode(pins[2], pigpio.OUTPUT)
        pi.set_mode(pins[3], pigpio.OUTPUT)
        self.pins = pins
        self.power = kwargs.get('power', None)
        self.pi = pi
        self.delayAfterStep = kwargs.get('delayAfterStep', 0.000003)
        self.deque = deque(kwargs.get('sequence', fullStepSequence))
        
    def setDelay(self):
        while True:
            self.cc_step()
            self.c_step()
            self.delayAfterStep = self.delayAfterStep + 0.01
            print(self.delayAfterStep)

    def cc_step(self):
        """
        Counter clockwise step
        """
        for i in range(20):
            self.deque.rotate(-1)
            self.do_step(self.deque[0])

    def c_step(self):
        """
        Clockwise step
        """
        for i in range(20):
            self.deque.rotate(1)
            self.do_step(self.deque[0])

    def do_step(self, step):
        #print(self.deque)
        if self.power:
            self.power.use()
        #self.clear_pins()        
        self.pi.write(self.pins[0], step[0])
        self.pi.write(self.pins[1], step[1])
        self.pi.write(self.pins[2], step[2])
        self.pi.write(self.pins[3], step[3])
        sleep(self.delayAfterStep)
        if self.power:
            self.power.release()
            #self.clear_pins()
    
    def clear_pins(self):
        self.pi.write(self.pins[0], 0)
        self.pi.write(self.pins[1], 0)
        self.pi.write(self.pins[2], 0)
        self.pi.write(self.pins[3], 0)

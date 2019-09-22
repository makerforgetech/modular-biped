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


class StepperMotor:

    def __init__(self, pin1, pin2, pin3, pin4, **kwargs):
        pi = pigpio.pi()  # modified to include pigpio reference directly
        pi.set_mode(pin1, pigpio.OUTPUT)
        pi.set_mode(pin2, pigpio.OUTPUT)
        pi.set_mode(pin3, pigpio.OUTPUT)
        pi.set_mode(pin4, pigpio.OUTPUT)
        self.pin1 = pin1
        self.pin2 = pin2
        self.pin3 = pin3
        self.pin4 = pin4
        self.power = kwargs.get('power', None)
        self.pi = pi
        self.delayAfterStep = kwargs.get('delayAfterStep', 0.0025)
        self.deque = deque(kwargs.get('sequence', halfStepSequence))

    def doСounterclockwiseStep(self):
        self.deque.rotate(-1)
        self.doStepAndDelay(self.deque[0])

    def doСlockwiseStep(self):
        self.deque.rotate(1)
        self.doStepAndDelay(self.deque[0])

    def doStepAndDelay(self, step):
        if self.power:
            self.power.use()
        self.pi.write(self.pin1, step[0])
        self.pi.write(self.pin2, step[1])
        self.pi.write(self.pin3, step[2])
        self.pi.write(self.pin4, step[3])
        sleep(self.delayAfterStep)
        if self.power:
            self.power.release()

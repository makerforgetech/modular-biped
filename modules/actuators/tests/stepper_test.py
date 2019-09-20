from modules.mocks.mock_pigpio import MockPiGPIO
from modules.mocks import mock_time
from modules.actuators.stepper import StepperMotor
import pytest

from collections import deque
from modules.power import Power

def test_init():
    power = Power(0)
    stepper = StepperMotor(0, 1, 2, 3, power)
    assert 0 == stepper.pin1
    assert 1 == stepper.pin2
    assert 2 == stepper.pin3
    assert 3 == stepper.pin4
    assert stepper.pi is not None
    assert stepper.delayAfterStep == 0.0025
    assert stepper.deque is not None


def test_doСounterclockwiseStep():
    power = Power(0)
    stepper = StepperMotor(0, 1, 2, 3, power)
    # stepper.doСounterclockwiseStep()
    assert True  # @todo how to test this?


def test_doСlockwiseStep():
    power = Power(0)
    stepper = StepperMotor(0, 1, 2, 3, power)
    # stepper.doСlockwiseStep()
    assert True  # @todo how to test this?



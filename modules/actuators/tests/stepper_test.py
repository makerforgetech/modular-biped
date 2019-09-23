from modules.mocks.mock_pigpio import MockPiGPIO
from modules.mocks import mock_time
from modules.actuators.stepper import StepperMotor
import pytest

from collections import deque

def test_init():
    stepper = StepperMotor((0, 1, 2, 3))
    assert 0 == stepper.pins[0]
    assert 1 == stepper.pins[1]
    assert 2 == stepper.pins[2]
    assert 3 == stepper.pins[3]
    assert stepper.pi is not None
    assert stepper.delayAfterStep == 0.0025
    assert stepper.deque is not None


def test_doСounterclockwiseStep():
    stepper = StepperMotor((0, 1, 2, 3))
    # stepper.cc_step()
    assert True  # @todo how to test this?


def test_doСlockwiseStep():
    stepper = StepperMotor((0, 1, 2, 3))
    # stepper.c_step()
    assert True  # @todo how to test this?



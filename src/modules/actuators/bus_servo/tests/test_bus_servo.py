import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock the SDK modules
mock_st_sdk = MagicMock()
mock_sc_sdk = MagicMock()
sys.modules['modules.actuators.bus_servo.STservo_sdk'] = mock_st_sdk
sys.modules['modules.actuators.bus_servo.SCservo_sdk'] = mock_sc_sdk

from modules.actuators.bus_servo.bus_servo import Servo

class TestBusServo(unittest.TestCase):

    def test_init(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        self.assertEqual(servo.identifier, 'test')
        self.assertEqual(servo.index, 1)
        self.assertEqual(servo.range, [0, 4095])
        self.assertEqual(servo.model, 'ST3215')

    def test_init_defaults(self):
        servo = Servo(name='test', id=1, range=[0, 1023])
        self.assertEqual(servo.baudrate, 1000000)
        self.assertEqual(servo.port, '/dev/ttyAMA0')

    def test_is_moving_true_when_mismatch_to_target(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        servo.pos = 3396
        servo.get_moving = MagicMock(return_value=0)
        servo.get_position = MagicMock(return_value=3047)
        servo.log = MagicMock()

        self.assertTrue(servo.is_moving())
        servo.log.assert_called_once()

    def test_is_moving_false_when_within_tolerance(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        servo.pos = 3396
        servo.get_moving = MagicMock(return_value=0)
        servo.get_position = MagicMock(return_value=3390)

        self.assertFalse(servo.is_moving())

if __name__ == '__main__':
    unittest.main()

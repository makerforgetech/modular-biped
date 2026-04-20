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
    def setUp(self):
        Servo._shared_port_handlers = {}
        Servo._shared_port_locks = {}
        Servo._shared_port_refcounts = {}
        mock_st_sdk.reset_mock()
        mock_sc_sdk.reset_mock()

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
        servo.log.assert_called_once_with(
            "Servo test is not reporting as moving but position 3047 does not match target position 3396",
            level='warning'
        )

    def test_is_moving_false_when_within_tolerance(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        servo.pos = 3396
        servo.get_moving = MagicMock(return_value=0)
        servo.get_position = MagicMock(return_value=3390)
        servo.log = MagicMock()

        self.assertFalse(servo.is_moving())
        servo.log.assert_not_called()

    def test_shared_port_handler_per_port_and_baudrate(self):
        Servo(name='test1', id=1, range=[0, 4095], model='ST3215')
        Servo(name='test2', id=2, range=[0, 4095], model='ST3215')
        mock_st_sdk.PortHandler.assert_called_once_with('/dev/ttyAMA0')

    def test_exit_closes_shared_port_only_once(self):
        servo1 = Servo(name='test1', id=1, range=[0, 4095], model='ST3215')
        servo2 = Servo(name='test2', id=2, range=[0, 4095], model='ST3215')
        port_handler = servo1.portHandler
        servo1.detach = MagicMock()
        servo2.detach = MagicMock()

        servo1.exit()
        port_handler.closePort.assert_not_called()
        servo2.exit()
        port_handler.closePort.assert_called_once()

if __name__ == '__main__':
    unittest.main()

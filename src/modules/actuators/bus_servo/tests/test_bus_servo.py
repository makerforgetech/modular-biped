import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock the SDK modules
mock_st_sdk = MagicMock()
mock_sc_sdk = MagicMock()
sys.modules['modules.actuators.bus_servo.STservo_sdk'] = mock_st_sdk
sys.modules['modules.actuators.bus_servo.SCservo_sdk'] = mock_sc_sdk

from modules.actuators.bus_servo.bus_servo import Servo
from modules.actuators.bus_servo import bus_servo as bus_servo_module

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
        self.assertEqual(servo.speed, 0)

    def test_is_moving_returns_false_when_get_moving_returns_zero(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        servo.pos = 3396
        servo.get_moving = MagicMock(return_value=0)
        servo.get_position = MagicMock(return_value=3047)
        servo.log = MagicMock()

        self.assertFalse(servo.is_moving())
        servo.get_position.assert_not_called()
        servo.log.assert_not_called()

    def test_is_moving_returns_true_when_get_moving_returns_one(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        servo.get_moving = MagicMock(return_value=1)
        self.assertTrue(servo.is_moving())

    def test_execute_with_retries_retries_port_busy_then_succeeds(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        operation = MagicMock(side_effect=[(-1, 0), (0, 0)])
        with patch.object(bus_servo_module, 'COMM_PORT_BUSY', -1), \
             patch.object(bus_servo_module, 'COMM_RX_TIMEOUT', -6), \
             patch('modules.actuators.bus_servo.bus_servo.time.sleep') as mock_sleep:
            result = servo._execute_with_retries(operation, max_attempts=3, retry_delay=0)
        self.assertEqual(result, (0, 0))
        self.assertEqual(operation.call_count, 2)
        mock_sleep.assert_called_once_with(0)

    def test_execute_with_retries_returns_immediately_on_success(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        operation = MagicMock(return_value=(0, 0))
        with patch.object(bus_servo_module, 'COMM_PORT_BUSY', -1), \
             patch.object(bus_servo_module, 'COMM_RX_TIMEOUT', -6), \
             patch('modules.actuators.bus_servo.bus_servo.time.sleep') as mock_sleep:
            result = servo._execute_with_retries(operation, max_attempts=3, retry_delay=0)
        self.assertEqual(result, (0, 0))
        self.assertEqual(operation.call_count, 1)
        mock_sleep.assert_not_called()

    def test_execute_with_retries_returns_failure_after_max_attempts(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        operation = MagicMock(return_value=(-1, 0))
        with patch.object(bus_servo_module, 'COMM_PORT_BUSY', -1), patch.object(bus_servo_module, 'COMM_RX_TIMEOUT', -6):
            result = servo._execute_with_retries(operation, max_attempts=3, retry_delay=0)
        self.assertEqual(result, (-1, 0))
        self.assertEqual(operation.call_count, 3)

    def test_execute_with_retries_applies_retry_delay(self):
        servo = Servo(name='test', id=1, range=[0, 4095], model='ST3215')
        operation = MagicMock(side_effect=[(-1, 0), (0, 0)])
        with patch.object(bus_servo_module, 'COMM_PORT_BUSY', -1), \
             patch.object(bus_servo_module, 'COMM_RX_TIMEOUT', -6), \
             patch('modules.actuators.bus_servo.bus_servo.time.sleep') as mock_sleep:
            result = servo._execute_with_retries(operation, max_attempts=3, retry_delay=0.01)
        self.assertEqual(result, (0, 0))
        mock_sleep.assert_called_once_with(0.01)

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

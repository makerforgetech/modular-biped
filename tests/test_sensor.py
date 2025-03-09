import unittest
from unittest.mock import patch, MagicMock

# Mock gpiozero and pubsub libraries
import sys
sys.modules['gpiozero'] = MagicMock()
sys.modules['pubsub'] = MagicMock()
sys.modules['pubsub.pub'] = MagicMock()

from modules.sensor import Sensor

class TestSensor(unittest.TestCase):
    def setUp(self):
        self.pin = 4
        self.sensor = Sensor(pin=self.pin)

    @patch('modules.sensor.MotionSensor')
    def test_init(self, MockMotionSensor):
        sensor_instance = MockMotionSensor.return_value
        sensor = Sensor(pin=self.pin)
        self.assertEqual(sensor.pin, self.pin)
        self.assertEqual(sensor.sensor, sensor_instance)

    @patch('modules.sensor.MotionSensor')
    def test_read(self, MockMotionSensor):
        sensor_instance = MockMotionSensor.return_value
        sensor_instance.motion_detected = True
        sensor = Sensor(pin=self.pin)
        self.assertTrue(sensor.read())
        self.assertTrue(sensor.value)

    @patch('modules.sensor.MotionSensor')
    def test_read_no_motion(self, MockMotionSensor):
        sensor_instance = MockMotionSensor.return_value
        sensor_instance.motion_detected = False
        sensor = Sensor(pin=self.pin)
        self.assertFalse(sensor.read())
        self.assertFalse(sensor.value)

    @patch('modules.sensor.MotionSensor')
    @patch('pubsub.pub.subscribe')
    def test_loop_subscription(self, mock_subscribe, MockMotionSensor):
        sensor = Sensor(pin=self.pin)
        mock_subscribe.assert_called_once_with(sensor.loop, 'loop:1')

    @patch('modules.sensor.MotionSensor')
    @patch('pubsub.pub.sendMessage')
    def test_loop(self, mock_sendMessage, MockMotionSensor):
        sensor_instance = MockMotionSensor.return_value
        sensor_instance.motion_detected = True
        self.sensor.loop()
        mock_sendMessage.assert_called_once_with('motion')

if __name__ == '__main__':
    unittest.main()
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

if __name__ == '__main__':
    unittest.main()
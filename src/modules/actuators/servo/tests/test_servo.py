import sys
import unittest
from unittest.mock import MagicMock, patch

mock_pigpio = MagicMock()
sys.modules['pigpio'] = mock_pigpio

# Mock ArduinoSerial
mock_arduino = MagicMock()
sys.modules['modules.network.arduinoserial'] = MagicMock()
sys.modules['modules.network.arduinoserial.arduinoserial'] = MagicMock()

from modules.actuators.servo.servo import Servo

class TestServo(unittest.TestCase):

    def test_init(self):
        servo = Servo(pin=1, name='test', range=[0, 180], start=50, serial=True)
        self.assertEqual(servo.pin, 1)
        self.assertEqual(servo.identifier, 'test')
        self.assertEqual(servo.range, [0, 180])

    def test_translate(self):
        servo = Servo(name='test', range=[0, 200], start=50, serial=True)
        # 50% of range [0,200] should be 100
        self.assertEqual(servo.translate(50), 100)

if __name__ == '__main__':
    unittest.main()

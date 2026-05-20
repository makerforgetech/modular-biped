import sys
import unittest
from unittest.mock import MagicMock, patch

mock_adafruit = MagicMock()
sys.modules['adafruit_servokit'] = mock_adafruit

from modules.i2c_servo.i2c_servo import I2CServo

class TestI2CServo(unittest.TestCase):

    def test_init(self):
        servo = I2CServo(servo_count=3)
        self.assertEqual(servo.count, 3)
        mock_adafruit.ServoKit.assert_called_with(channels=16)

if __name__ == '__main__':
    unittest.main()

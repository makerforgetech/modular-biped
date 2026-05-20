import sys
import unittest
from unittest.mock import MagicMock, patch

mock_gpiozero = MagicMock()
sys.modules['gpiozero'] = mock_gpiozero

from modules.actuators.piservo.piservo import PiServo

class TestPiServo(unittest.TestCase):

    def test_init(self):
        servo = PiServo(pin=22, range=[-40, 40], start=0)
        self.assertEqual(servo.pin, 22)
        self.assertEqual(servo.range, [-40, 40])
        self.assertEqual(servo.start, 0)

    def test_setup_messaging(self):
        servo = PiServo(pin=22, range=[-40, 40], start=0)
        with patch.object(servo, 'subscribe') as mock_sub:
            servo.setup_messaging()
            mock_sub.assert_called_with('piservo/move', servo.move)

if __name__ == '__main__':
    unittest.main()

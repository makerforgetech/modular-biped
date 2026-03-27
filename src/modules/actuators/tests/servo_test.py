import sys
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

# Mock hardware dependencies before importing Servo
sys.modules['yaml'] = MagicMock()
sys.modules['pigpio'] = MagicMock()
sys.modules['modules.network.arduinoserial'] = MagicMock()
sys.modules['modules.network.arduinoserial.arduinoserial'] = MagicMock()

from modules.actuators.servo.servo import Servo


class ServoTest(unittest.TestCase):

    def _make_servo(self, **kwargs):
        sv = Servo(**kwargs)
        sv._messaging_service = MagicMock()
        return sv

    def test_init(self):
        # Pin 1, default values
        sv = Servo(pin=1, name='test', range=(20000, 40000), serial=True)
        assert sv.pos == 30000
        assert sv.range == (20000, 40000)
        assert sv.pin == 1

        # Override defaults
        sv = Servo(pin=10, name='test', range=(10, 40), start=50, serial=True)
        assert sv.pos == 25
        assert sv.range == (10, 40)
        assert sv.pin == 10

    def test_move(self):
        sv = self._make_servo(pin=1, name='test', range=(0, 200), start=50, serial=None)
        # test absolute values
        sv.move(10)
        assert sv.pos == 20
        sv.move(20)
        assert sv.pos == 40
        sv.move(50)
        assert sv.pos == 100

        # test boundary values
        sv.move(0)
        assert sv.pos == 0
        sv.move(100)
        assert sv.pos == 200

        sv.reset()
        assert sv.pos == 100

        # test out of range values
        with self.assertRaises(ValueError) as cm:
            sv.move(-10, False)
        assert "out of range" in str(cm.exception)
        with self.assertRaises(ValueError) as cm:
            sv.move(101, False)
        assert "out of range" in str(cm.exception)

        sv.move(-10)
        assert sv.pos == 0
        sv.move(181)
        assert sv.pos == 200

    def test_move_relative(self):
        sv = self._make_servo(pin=1, name='test', range=(0, 200), start=50, serial=None)
        # test relative values
        sv.move_relative(10)
        assert sv.pos == 120
        sv.move_relative(-20)
        assert sv.pos == 80

        # test out of range values
        with self.assertRaises(ValueError) as cm:
            sv.move_relative(-50, False)
        assert "out of range" in str(cm.exception)
        with self.assertRaises(ValueError) as cm:
            sv.move_relative(101, False)
        assert "out of range" in str(cm.exception)

        sv.move_relative(-50)
        assert sv.pos == 0
        sv.move_relative(101)
        assert sv.pos == 200

    def test_buffer(self):
        sv = self._make_servo(pin=1, name='test', range=(0, 2000), start=50, serial=None)
        sv.move(100)
        assert sv.pos == 2000

        sv2 = self._make_servo(pin=1, name='test', range=(0, 2000), start=50, buffer=100, serial=None)
        sv2.move(100)
        assert sv2.pos == 2000

        sv2.move(0)
        assert sv2.pos == 0

        sequence = sv.calculate_move(100, 200)
        assert len(sequence) == 1

        sequence = sv2.calculate_move(100, 200)
        assert len(sequence) == 10
        assert sequence[0][0] == 100
        assert sequence[9][0] == 200


if __name__ == '__main__':
    unittest.main()

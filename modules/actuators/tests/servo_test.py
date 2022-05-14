from unittest import TestCase, mock
from modules.mocks import mock_pigpio
from modules.mocks import mock_arduino_serial
from modules.actuators.servo import Servo
import pytest

@mock.patch('modules.actuators.servo.pub', return_value=mock.Mock())
class ServoTest(TestCase):

    def test_init(self, mock_pub):
        # Pin 1, default values
        sv = Servo(1, 'test', (20000, 40000))
        assert sv.pos == 30000
        assert sv.range == (20000, 40000)
        assert sv.pin == 1

        # Override defaults
        sv = Servo(10, 'test', (10, 40), start_pos=50)
        assert sv.pos == 25
        assert sv.range == (10, 40)
        assert sv.pin == 10


    def test_move(self, mock_pub):
        sv = Servo(1, 'test', (0, 200), start_pos=50)
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
        with pytest.raises(ValueError) as ex:
            sv.move(-10, False)
        assert "out of range" in str(ex.value)
        with pytest.raises(ValueError) as ex:
            sv.move(101, False)
        assert "out of range" in str(ex.value)

        sv.move(-10)
        assert sv.pos == 0
        sv.move(181)
        assert sv.pos == 200


    def test_move_relative(self, mock_pub):
        sv = Servo(1, 'test', (0, 200), start_pos=50)
        # test absolute values
        sv.move_relative(10)
        assert sv.pos == 120
        sv.move_relative(-20)
        assert sv.pos == 80

        # test out of range values
        with pytest.raises(ValueError) as ex:
            sv.move_relative(-50, False)
        assert "out of range" in str(ex.value)
        with pytest.raises(ValueError) as ex:
            sv.move_relative(101, False)
        assert "out of range" in str(ex.value)

        sv.move_relative(-50)
        assert sv.pos == 0
        sv.move_relative(101)
        assert sv.pos == 200


    def test_buffer(self, mock_pub):
        sv = Servo(1, 'test', (0, 2000), start_pos=50)
        sv.move(100)
        assert sv.pos == 2000

        sv2 = Servo(1, 'test', (0, 2000), start_pos=50, buffer=100)
        sv2.move(100)
        assert sv2.pos == 2000

        sv2.move(0)
        assert sv2.pos == 0

        sequence = sv.calculate_move(100, 200)
        assert len(sequence) == 1

        sequence = sv2.calculate_move(100, 200)
        # [(100, 0.1), (101.5, 0.1), (103.75, 0.1), (107.125, 0.1), (112.1875, 0.1), (119.78125, 0.1), (131.171875, 0.1), (148.2578125, 0.1), (173.88671875, 0.1), (200, 0.1)]
        assert len(sequence) == 10
        assert sequence[0][0] == 100
        assert sequence[9][0] == 200


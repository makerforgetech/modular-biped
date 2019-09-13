import modules.mock_pigpio
import modules.mock_time
from modules.servo import Servo
import pytest


def test_init():
    # Pin 1, default values
    sv = Servo(1, (20000, 40000))
    assert sv.pos == 30000
    assert sv.range == (20000, 40000)
    assert sv.pin == 1

    assert sv.pi is not None
    assert sv.pi.setmode_called == 1

    # Override defaults
    sv = Servo(10, (10, 40), 50)
    assert sv.pos == 25
    assert sv.range == (10, 40)
    assert sv.pin == 10


def test_move():
    sv = Servo(1, (0, 200), 50)
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

    # test out of range values
    with pytest.raises(ValueError) as ex:
        sv.move(-10)
    assert "out of range" in str(ex.value)
    with pytest.raises(ValueError) as ex:
        sv.move(101)
    assert "out of range" in str(ex.value)


def test_buffer():
    sv = Servo(1, (0, 2000), 50)
    sv.move(100)
    assert sv.pos == 2000

    sv = Servo(1, (0, 2000), 50, 100)
    sv.move(100)
    assert sv.pos == 2000

    sv.move(0)
    assert sv.pos == 0

    sv = Servo(1, (1560, 1880), 40, 100)
    sv.move(30)
    assert sv.pos == 1656

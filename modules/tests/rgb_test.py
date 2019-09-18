from modules.mocks.mock_pigpio import MockPiGPIO
from modules.rgb import RGB


def test_init():
    led = RGB(24, 23, 18)
    assert led.r == 24
    assert led.g == 23
    assert led.b == 18
    assert led.pi is not None
    assert led.pi.setmode_called == 3

def test_reset():
    led = RGB(0, 1, 2)
    led.led(0, 100)
    led.reset()

    assert True  # @todo


def test_breathe():
    led = RGB(0, 1, 2)
    led.breathe(0)

    assert True  # @todo

import modules.mock_pigpio
import modules.mock_time
from modules.rgb import RGB
import pytest

def test_init():
    led = RGB(24, 23, 18)
    assert led.r == 24
    assert led.g == 23
    assert led.b == 18
    assert led.pi is not None
    assert led.pi.setmode_called == 3

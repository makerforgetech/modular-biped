from unittest import TestCase, mock
from modules.mocks import mock_pigpio  # as this can't be installed
from modules.rgb import RGB


@mock.patch('modules.rgb.pigpio', return_value=mock.Mock())
class TestRGB(TestCase):
    def test_init(self, mock_pigpio):
        led = RGB(24, 23, 18)
        assert led.r == 24
        assert led.g == 23
        assert led.b == 18


    def test_reset(self, mock_pigpio):
        led = RGB(0, 1, 2)
        led.led(0, 100)
        led.reset()

        assert True  # @todo


    # def test_breathe(self):
    #     led = RGB(0, 1, 2)
    #     led.breathe(0)
    #
    #     assert True  # @todo

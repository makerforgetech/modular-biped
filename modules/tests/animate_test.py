from modules.mocks.mock_pigpio import MockPiGPIO
from modules.mocks import mock_time
from modules.mocks import mock_pubsub
from modules.mocks import mock_arduino_serial
from modules.animate import Animate
from modules.actuators.servo import Servo

def test_init():
    path = '../../animations'
    animate = Animate(path=path)
    assert animate.path == path + '/'
#
# def test_animate():
#     path = '../../animations'
#     animate = Animate(path=path)
#     animate.animate('head_shake')
#     animate.animate('head_swirl')


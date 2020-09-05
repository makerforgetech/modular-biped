from modules.mocks.mock_pigpio import MockPiGPIO
from modules.mocks.mock_time import sleep
from modules.animate import Animate
from modules.actuators.servo import Servo


# @todo mouse_recorder files should end with ] not , and have double quotes.

def test_init():
    pan = Servo(1, (0, 100))
    tilt = Servo(1, (0, 100))
    path = '../animations'
    animate = Animate(pan, tilt, path=path)

    assert animate.pan == pan
    assert animate.tilt == tilt
    assert animate.path == path + '/'


def test_translate():
    pan = Servo(1, (0, 100))
    tilt = Servo(1, (0, 100))
    path = '../animations'
    animate = Animate(pan, tilt, path=path)
    assert 0 == animate.map(-1)
    assert 25 == animate.map(-0.5)
    assert 50 == animate.map(0)
    assert 75 == animate.map(0.5)
    assert 100 == animate.map(1)


# def test_animate():
#     pan = Servo(1, (0, 100))
#     tilt = Servo(1, (0, 100))
#     path = '../animations'
#     animate = Animate(pan, tilt, path=path)
#     animate.animate('head_shake')
#     animate.animate('head_swirl')


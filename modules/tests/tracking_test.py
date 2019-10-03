from modules.mocks.mock_cv2 import MockCV2
from modules.tracking import Tracking
from modules.actuators.servo import Servo
from modules.vision import Vision

def test_init():
    pan = Servo(1, (0, 100))
    tilt = Servo(1, (0, 100))
    vision = Vision()
    tracking = Tracking(vision, pan, tilt)
    assert tracking.vision == vision
    assert tracking.pan == pan
    assert tracking.tilt == tilt
    assert tracking.bounds_percent == 15
    assert tracking.bounds == vision.dimensions[0] / (100 / 15)
    assert set(vision.lines) == set([((96, 0), (96, 480)), ((544, 0), (544, 480)), ((0, 96), (640, 96)), ((0, 384), (640, 384))])


def test_track_largest_match():
    pan = Servo(1, (0, 100))
    tilt = Servo(1, (0, 100))
    vision = Vision()
    tracking = Tracking(vision, pan, tilt)
    tracking.track_largest_match()
    # @todo add data to vision.detect() mock response to test further


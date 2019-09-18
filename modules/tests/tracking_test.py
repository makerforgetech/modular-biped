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
    assert tracking.bounds_percent == 25
    assert tracking.bounds == vision.dimensions[0] / (100 / 25)
    assert set(vision.lines) == set([((160.0, 0), (160.0, 480)), ((480.0, 0), (480.0, 480)), ((0, 160.0), (640, 160.0)), ((0, 320.0), (640, 320.0))])


def test_track_largest_match():
    pan = Servo(1, (0, 100))
    tilt = Servo(1, (0, 100))
    vision = Vision()
    tracking = Tracking(vision, pan, tilt)
    tracking.track_largest_match()
    # @todo add data to vision.detect() mock response to test further


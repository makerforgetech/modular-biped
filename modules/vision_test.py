import modules.mock_cv2
from modules.vision import Vision
import pytest


def test_basic_config():
    vision = Vision()
    assert vision.mode == Vision.MODE_MOTION
    assert vision.index == 0
    assert type(vision.video).__name__ == 'MockVideoCapture'
    assert not vision.static_back
    assert not vision.preview
    assert vision.dimensions == (640, 480)
    assert vision.lines == []
    assert not hasattr(vision, 'cascade')


def test_basic_config_face():
    vision = Vision(Vision.MODE_FACES)
    assert vision.mode == Vision.MODE_FACES
    assert vision.index == 0
    assert type(vision.video).__name__ == 'MockVideoCapture'
    assert not vision.static_back
    assert not vision.preview
    assert vision.dimensions == (640, 480)
    assert vision.lines == []
    assert vision.cascade is not None


def test_detect():
    vision = Vision()
    matches = vision.detect()
    assert vision.static_back is not None
    assert matches is None

    matches = vision.detect()
    assert matches is not None


def test_detect_faces():
    vision = Vision(Vision.MODE_FACES)
    matches = vision.detect()
    assert vision.static_back is None
    assert matches is not None

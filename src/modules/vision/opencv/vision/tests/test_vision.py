import sys
import unittest
from unittest.mock import MagicMock, patch

for mod in ['cv2', 'numpy', 'picamera2', 'argparse']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from modules.vision.opencv.vision.vision import Vision

class TestOpenCVVision(unittest.TestCase):

    def test_class_exists(self):
        self.assertTrue(hasattr(Vision, '__init__'))

    def test_setup_messaging(self):
        v = Vision.__new__(Vision)
        with patch.object(v, 'subscribe') as mock_sub:
            v.setup_messaging()
            mock_sub.assert_not_called()

    def test_loop_calls_scan(self):
        v = Vision.__new__(Vision)
        with patch.object(v, 'scan') as mock_scan:
            v.loop()
            mock_scan.assert_called_once()

if __name__ == '__main__':
    unittest.main()

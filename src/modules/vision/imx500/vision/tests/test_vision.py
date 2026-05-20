import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock hardware-specific modules
for mod in ['cv2', 'numpy', 'picamera2', 'libcamera', 'argparse']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()
sys.modules['picamera2.devices'] = MagicMock()
sys.modules['picamera2.devices.imx500'] = MagicMock()
sys.modules['picamera2.devices.imx500.imx500_postprocess'] = MagicMock()
sys.modules['numpy'] = MagicMock()

from modules.vision.imx500.vision.vision import Vision

class TestIMX500Vision(unittest.TestCase):

    def test_class_exists(self):
        self.assertTrue(hasattr(Vision, '__init__'))

    def test_setup_messaging(self):
        v = Vision.__new__(Vision)
        with patch.object(v, 'subscribe') as mock_sub, \
             patch.object(v, 'publish') as mock_pub:
            v.setup_messaging()
            # Should subscribe to system topics

if __name__ == '__main__':
    unittest.main()

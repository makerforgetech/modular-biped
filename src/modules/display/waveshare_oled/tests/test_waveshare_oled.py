import sys
import unittest
from unittest.mock import MagicMock, patch

mock_pil = MagicMock()
sys.modules['PIL'] = mock_pil
sys.modules['PIL.Image'] = mock_pil.Image
sys.modules['PIL.ImageDraw'] = mock_pil.ImageDraw
sys.modules['PIL.ImageFont'] = mock_pil.ImageFont

mock_waveshare = MagicMock()
sys.modules['modules.display.lib.waveshare'] = mock_waveshare
sys.modules['modules.display.lib.waveshare.OLED_0in91'] = mock_waveshare.OLED_0in91
mock_waveshare.OLED_0in91.OLED_0in91.return_value.width = 128
mock_waveshare.OLED_0in91.OLED_0in91.return_value.height = 32

from modules.display.waveshare_oled.waveshare_oled import WaveshareOLED

class TestWaveshareOLED(unittest.TestCase):

    def test_init(self):
        oled = WaveshareOLED(test_on_boot=False)
        # init should not raise

    def test_setup_messaging(self):
        oled = WaveshareOLED()
        with patch.object(oled, 'subscribe') as mock_sub:
            oled.setup_messaging()
            mock_sub.assert_any_call('system/exit', oled.exit)

if __name__ == '__main__':
    unittest.main()

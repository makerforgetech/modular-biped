import sys
import unittest
from unittest.mock import MagicMock, patch

mock_spi = MagicMock()
mock_pil = MagicMock()
mock_lcd = MagicMock()
mock_lcd_module = MagicMock()
sys.modules['spidev'] = mock_spi
sys.modules['PIL'] = mock_pil
sys.modules['PIL.Image'] = mock_pil.Image
sys.modules['PIL.ImageDraw'] = mock_pil.ImageDraw
sys.modules['modules.display.lib'] = mock_lcd
sys.modules['modules.display.lib.LCD_1inch28'] = mock_lcd_module

# Mock the TFTDisplay parent
mock_tft_display_mod = MagicMock()
sys.modules['modules.display.tft_display'] = mock_tft_display_mod

# Make TFTDisplay a usable base class
class MockTFTDisplay(MagicMock):
    pass
mock_tft_display_mod.TFTDisplay = MockTFTDisplay

from modules.display.tft_display_eye.tft_display_eye import TFTDisplayEye

class TestTFTDisplayEye(unittest.TestCase):

    def test_class_exists(self):
        self.assertTrue(hasattr(TFTDisplayEye, '__init__'))

if __name__ == '__main__':
    unittest.main()

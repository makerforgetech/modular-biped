import sys
import unittest
from unittest.mock import MagicMock, patch

mock_board = MagicMock()
mock_colour = MagicMock()
mock_seesaw = MagicMock()
sys.modules['board'] = mock_board
sys.modules['colour'] = mock_colour
sys.modules['adafruit_seesaw'] = mock_seesaw

# Mock Color class to return empty list for range_to
mock_colour.Color.return_value.range_to.return_value = []

from modules.neopixel.neopx.neopx import NeoPx

class TestNeoPx(unittest.TestCase):

    def test_color_map_exists(self):
        self.assertIn('red', NeoPx.COLOR_MAP)
        self.assertIn('green', NeoPx.COLOR_MAP)
        self.assertIn('blue', NeoPx.COLOR_MAP)
        self.assertIn('off', NeoPx.COLOR_MAP)

    def test_setup_messaging(self):
        px = NeoPx.__new__(NeoPx)
        with patch.object(px, 'subscribe') as mock_sub:
            px.setup_messaging()
            mock_sub.assert_any_call('led', px.set)

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch
from modules.audio.braillespeak.braillespeak import BrailleSpeak

class TestBrailleSpeak(unittest.TestCase):

    def test_init(self):
        bs = BrailleSpeak(pin=27, duration=0.05)
        self.assertEqual(bs.pin, 27)
        self.assertEqual(bs.duration, 0.05)
        self.assertEqual(len(bs.notes), 8)

    def test_setup_messaging(self):
        bs = BrailleSpeak(pin=27)
        with patch.object(bs, 'subscribe') as mock_sub:
            bs.setup_messaging()
            mock_sub.assert_called_with('speak', bs.send)

if __name__ == '__main__':
    unittest.main()

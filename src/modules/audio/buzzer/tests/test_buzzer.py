import sys
import unittest
from unittest.mock import MagicMock, patch

mock_gpiozero = MagicMock()
sys.modules['gpiozero'] = mock_gpiozero
sys.modules['gpiozero.tones'] = mock_gpiozero.tones

from modules.audio.buzzer.buzzer import Buzzer

class TestBuzzer(unittest.TestCase):

    def test_init(self):
        buzzer = Buzzer(pin=27)
        self.assertEqual(buzzer.pin, 27)
        mock_gpiozero.TonalBuzzer.assert_called_with(27)

    def test_setup_messaging(self):
        buzzer = Buzzer(pin=27)
        with patch.object(buzzer, 'subscribe') as mock_sub:
            buzzer.setup_messaging()
            mock_sub.assert_any_call('play', buzzer.play_song)
            mock_sub.assert_any_call('buzz', buzzer.buzz)

if __name__ == '__main__':
    unittest.main()

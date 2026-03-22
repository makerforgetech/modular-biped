import sys
import unittest
from unittest.mock import MagicMock, patch

mock_pyttsx3 = MagicMock()
mock_elevenlabs = MagicMock()
sys.modules['pyttsx3'] = mock_pyttsx3
sys.modules['elevenlabs'] = mock_elevenlabs

from modules.audio.ttsmodule.ttsmodule import TTSModule

class TestTTSModule(unittest.TestCase):

    def test_init_pyttsx3(self):
        tts = TTSModule(service='pyttsx3')
        self.assertEqual(tts.service, 'pyttsx3')

    def test_setup_messaging(self):
        tts = TTSModule(service='pyttsx3')
        with patch.object(tts, 'subscribe') as mock_sub:
            tts.setup_messaging()
            mock_sub.assert_called_with('tts', tts.speak)

if __name__ == '__main__':
    unittest.main()

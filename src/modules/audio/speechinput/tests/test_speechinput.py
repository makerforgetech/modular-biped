import sys
import unittest
from unittest.mock import MagicMock, patch

mock_speech_recognition = MagicMock()
mock_recognizer = MagicMock()
mock_microphone = MagicMock()
mock_speech_recognition.Recognizer.return_value = mock_recognizer
mock_speech_recognition.Microphone.return_value = mock_microphone
sys.modules['speech_recognition'] = mock_speech_recognition

from modules.audio.speechinput.speechinput import SpeechInput

class TestSpeechInput(unittest.TestCase):

    def test_init(self):
        si = SpeechInput(device_name='test', sample_rate=16000)
        self.assertEqual(si.device_name, 'test')
        self.assertEqual(si.sample_rate, 16000)
        self.assertFalse(si.listening)

    def test_setup_messaging(self):
        si = SpeechInput()
        si.log = MagicMock()
        with patch.object(si, 'subscribe') as mock_sub:
            si.setup_messaging()
            mock_sub.assert_any_call('speech:listen', si.start)

if __name__ == '__main__':
    unittest.main()

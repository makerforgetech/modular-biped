import sys
import unittest
from unittest.mock import MagicMock, patch

mock_transformers = MagicMock()
sys.modules['transformers'] = mock_transformers

from modules.neopixel.emotion_analysis.emotion_analysis import EmotionAnalysis

class TestEmotionAnalysis(unittest.TestCase):

    def test_init(self):
        ea = EmotionAnalysis(colors={'happy': 'green', 'sad': 'blue'})
        self.assertIsNotNone(ea.emotion_analyzer)
        self.assertIsNotNone(ea.emotion_to_keyword)

    def test_setup_messaging(self):
        ea = EmotionAnalysis()
        with patch.object(ea, 'subscribe') as mock_sub:
            ea.setup_messaging()
            mock_sub.assert_called_with('speech', ea.analyze_text)

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch

mock_googletrans = MagicMock()
mock_translator_instance = MagicMock()
mock_googletrans.Translator.return_value = mock_translator_instance

import sys
sys.modules['googletrans'] = mock_googletrans

from modules.translator.translator import Translator

class TestTranslator(unittest.TestCase):

    def test_init_defaults(self):
        t = Translator()
        self.assertEqual(t.src, 'en')
        self.assertEqual(t.dest, 'en')

    def test_same_language_no_translation(self):
        t = Translator(src='en', dest='en')
        result = t.request('hello')
        self.assertEqual(result, 'hello')

    def test_request(self):
        t = Translator(src='en', dest='es')
        mock_translation = MagicMock()
        mock_translation.text = 'hola'
        mock_translator_instance.translate.return_value = mock_translation
        result = t.request('hello')
        self.assertEqual(result, 'hola')

if __name__ == '__main__':
    unittest.main()

import sys
import unittest
from unittest.mock import MagicMock, patch

mock_telegram = MagicMock()
sys.modules['telegram'] = mock_telegram
sys.modules['telegram.ext'] = mock_telegram.ext

from modules.network.telegrambot.telegrambot import TelegramBot

class TestTelegramBot(unittest.TestCase):

    def test_init_no_token(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(RuntimeError):
                TelegramBot()

    def test_init_with_token(self):
            with patch.dict('os.environ', {}, clear=True):
                bot = TelegramBot(token='test_token_123')
                self.assertEqual(bot.token, 'test_token_123')

if __name__ == '__main__':
    unittest.main()

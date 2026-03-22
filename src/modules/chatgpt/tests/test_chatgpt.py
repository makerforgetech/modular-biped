import sys
import os
import unittest
from unittest.mock import MagicMock, patch

mock_openai = MagicMock()
sys.modules['openai'] = mock_openai

from modules.chatgpt.chatgpt import ChatGPT

class TestChatGPT(unittest.TestCase):

    def test_init_no_api_key(self):
        env = {k: v for k, v in os.environ.items() if k != 'OPENAI_API_KEY'}
        with patch.dict('os.environ', env, clear=True):
            with self.assertRaises(RuntimeError):
                ChatGPT()

    def test_init_with_api_key(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            bot = ChatGPT()
            self.assertEqual(bot.model, 'gpt-4o-mini')

    def test_setup_messaging(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            bot = ChatGPT()
            with patch.object(bot, 'subscribe') as mock_sub:
                bot.setup_messaging()
                mock_sub.assert_any_call('speech', bot.completion)

if __name__ == '__main__':
    unittest.main()

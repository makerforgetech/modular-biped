import unittest
from unittest.mock import MagicMock, patch
from modules.personality.personality import Personality

class TestPersonality(unittest.TestCase):

    def test_init_defaults(self):
        p = Personality()
        self.assertEqual(p.eye, 'blue')
        self.assertEqual(p.min_interval, 20)
        self.assertEqual(p.max_interval, 60)
        self.assertEqual(p.balance_enabled, True)
        self.assertIsNotNone(p.next_action_time)

    def test_init_custom(self):
        p = Personality(min_interval=10, max_interval=30, balance_enabled=False)
        self.assertEqual(p.min_interval, 10)
        self.assertEqual(p.max_interval, 30)
        self.assertFalse(p.balance_enabled)

    def test_calculate_next_action_time(self):
        p = Personality(min_interval=5, max_interval=10)
        t = p.calculate_next_action_time()
        self.assertIsNotNone(t)

if __name__ == '__main__':
    unittest.main()

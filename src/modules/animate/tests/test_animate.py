import unittest
from unittest.mock import MagicMock, patch
import sys

mock_gpiozero = MagicMock()
sys.modules['gpiozero'] = mock_gpiozero

from modules.animate.animate import Animate

class TestAnimate(unittest.TestCase):

    def test_init_default_path(self):
        anim = Animate()
        self.assertTrue(anim.path.endswith('/'))

    def test_animate_missing_file(self):
        anim = Animate(path='/tmp')
        anim.messaging_service = MagicMock()
        anim.log = MagicMock()
        with self.assertRaises(ValueError):
            anim.animate('nonexistent')

    def test_setup_messaging(self):
        anim = Animate(path='/tmp')
        with patch.object(anim, 'subscribe') as mock_sub:
            anim.setup_messaging()
            mock_sub.assert_called_with('animate', anim.animate)

if __name__ == '__main__':
    unittest.main()

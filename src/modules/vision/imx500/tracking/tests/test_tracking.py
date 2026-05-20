import unittest
from unittest.mock import MagicMock, patch
from modules.vision.imx500.tracking.tracking import Tracking

class TestTracking(unittest.TestCase):

    def test_init_defaults(self):
        t = Tracking()
        self.assertTrue(t.active)
        self.assertFalse(t.moving)
        self.assertEqual(t.filter, 'person')

    def test_init_custom(self):
        t = Tracking(active=False, filter='car')
        self.assertFalse(t.active)
        self.assertEqual(t.filter, 'car')

    def test_set_state(self):
        t = Tracking()
        t.set_state(False)
        self.assertFalse(t.active)

    def test_unfreeze(self):
        t = Tracking()
        t.moving = True
        t.unfreeze()
        self.assertFalse(t.moving)

    def test_setup_messaging(self):
        t = Tracking()
        with patch.object(t, 'subscribe') as mock_sub:
            t.setup_messaging()
            mock_sub.assert_any_call('vision/detections', t.handle)

if __name__ == '__main__':
    unittest.main()

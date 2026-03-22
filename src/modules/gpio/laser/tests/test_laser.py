import unittest
from unittest import mock

mock_gpiozero = mock.MagicMock()
with mock.patch.dict('sys.modules', {'gpiozero': mock_gpiozero}):
    from modules.gpio.laser.laser import Laser

class TestLaser(unittest.TestCase):

    def test_init(self):
        laser = Laser(pin=17)
        self.assertEqual(laser.pin, 17)
        mock_gpiozero.LED.assert_called_with(17)

    def test_activate(self):
        laser = Laser(pin=17)
        laser.activate(True)
        self.assertTrue(laser.state)
        laser.activate(False)
        self.assertFalse(laser.state)

    def test_toggle(self):
        laser = Laser(pin=17, state=False)
        laser.toggle()
        self.assertTrue(laser.state)
        laser.toggle()
        self.assertFalse(laser.state)

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest import mock

mock_gpiozero = mock.MagicMock()
with mock.patch.dict('sys.modules', {'gpiozero': mock_gpiozero}):
    from modules.gpio.read.read import Read

class TestRead(unittest.TestCase):

    def test_init(self):
        reader = Read(pin=17)
        self.assertEqual(reader.pin, 17)
        mock_gpiozero.InputDevice.assert_called_with(17)

    def test_read(self):
        reader = Read(pin=17)
        mock_gpiozero.InputDevice.return_value.value = 1
        result = reader.read()
        self.assertEqual(reader.value, 1)

if __name__ == '__main__':
    unittest.main()

import sys
import unittest
from unittest.mock import MagicMock, patch

mock_robust_serial = MagicMock()
sys.modules['modules.network.robust_serial'] = mock_robust_serial
sys.modules['modules.network.robust_serial.robust_serial'] = mock_robust_serial.robust_serial
sys.modules['modules.network.robust_serial.utils'] = mock_robust_serial.utils
mock_robust_serial.utils.open_serial_port.side_effect = Exception("No serial port")

from modules.network.arduinoserial.arduinoserial import ArduinoSerial

class TestArduinoSerial(unittest.TestCase):

    def test_init_no_port(self):
        with self.assertRaises(Exception):
            ArduinoSerial(port='/dev/ttyAMA0')

    def test_setup_messaging(self):
        arduino = ArduinoSerial.__new__(ArduinoSerial)
        arduino.serial_file = None
        with patch.object(arduino, 'subscribe') as mock_sub:
            arduino.setup_messaging()
            mock_sub.assert_called_with('serial', arduino.send)

if __name__ == '__main__':
    unittest.main()

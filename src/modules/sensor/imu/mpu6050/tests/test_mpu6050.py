import sys
import unittest
from unittest.mock import MagicMock, patch

mock_smbus = MagicMock()
mock_pubsub = MagicMock()
sys.modules['smbus'] = mock_smbus
sys.modules['pubsub'] = mock_pubsub
sys.modules['pubsub.pub'] = mock_pubsub.pub

with patch('time.sleep', return_value=None):
    from modules.sensor.imu.mpu6050.mpu6050 import MPU6050

class TestMPU6050(unittest.TestCase):

    def test_init(self):
        with patch('time.sleep', return_value=None):
            sensor = MPU6050()
        self.assertEqual(sensor.Device_Address, 0x68)
        mock_smbus.SMBus.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()

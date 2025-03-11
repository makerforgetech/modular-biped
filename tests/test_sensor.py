import unittest
from unittest import mock

# Mock the entire gpiozero module before Sensor gets imported
mock_gpiozero = mock.MagicMock()
mock_gpiozero.MotionSensor = mock.MagicMock()
with mock.patch.dict('sys.modules', {'gpiozero': mock_gpiozero}):
    from modules.sensor import Sensor

class TestSensor(unittest.TestCase):

    def test_init(self):
        # Test with pin and without test_on_boot
        sensor = Sensor(pin=17)
        self.assertEqual(sensor.pin, 17)
        self.assertEqual(sensor.sensor, mock_gpiozero.MotionSensor.return_value)
        mock_gpiozero.MotionSensor.assert_called_with(17)

        # Test with pin and test_on_boot
        with mock.patch.object(Sensor, 'test', return_value=None) as mock_test:
            sensor = Sensor(pin=18, test_on_boot=True)
            self.assertEqual(sensor.pin, 18)
            self.assertEqual(sensor.sensor, mock_gpiozero.MotionSensor.return_value)
            mock_gpiozero.MotionSensor.assert_called_with(18)
            mock_test.assert_called_once()

    def test_read(self):
        mock_sensor_instance = mock_gpiozero.MotionSensor.return_value
        mock_sensor_instance.motion_detected = True

        sensor = Sensor(pin=17)
        self.assertTrue(sensor.read())
        self.assertTrue(sensor.value)

        mock_sensor_instance.motion_detected = False
        self.assertFalse(sensor.read())
        self.assertFalse(sensor.value)

    def test_loop(self):
        sensor = Sensor(pin=17)
        with mock.patch.object(sensor, 'read', return_value=True):
            with mock.patch.object(sensor, 'publish') as mock_publish:
                sensor.loop()
                mock_publish.assert_called_with('motion')

        with mock.patch.object(sensor, 'read', return_value=False):
            with mock.patch.object(sensor, 'publish') as mock_publish:
                sensor.loop()
                mock_publish.assert_not_called()

    def test_setup_messaging(self):
        sensor = Sensor(pin=17)
        with mock.patch.object(sensor, 'subscribe') as mock_subscribe:
            sensor.setup_messaging()
            mock_subscribe.assert_called_with('system/loop/1', sensor.loop)

if __name__ == '__main__':
    unittest.main()

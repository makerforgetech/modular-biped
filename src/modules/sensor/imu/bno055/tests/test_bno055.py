import sys
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, call

# Mock hardware/external dependencies before importing BNO055.
# These are added directly to sys.modules (not via patch.dict) so they persist
# and the bno055 module stays registered in sys.modules for later string-based patching.
mock_board = MagicMock()
mock_adafruit_bno055 = MagicMock()
mock_pubsub = MagicMock()
sys.modules['board'] = mock_board
sys.modules['adafruit_bno055'] = mock_adafruit_bno055
sys.modules['pubsub'] = mock_pubsub
sys.modules['pubsub.pub'] = mock_pubsub.pub

from modules.sensor.imu.bno055.bno055 import BNO055


def make_sensor(**kwargs):
    """Helper to create a BNO055 with mocked hardware."""
    mock_adafruit_bno055.BNO055_I2C.reset_mock()
    mock_board.I2C.reset_mock()
    return BNO055(**kwargs)


SAMPLE_DATA = {
    'temperature': 20,
    'acceleration': (0.1, -9.8, 0.0),
    'magnetic': (10.0, 60.0, 30.0),
    'gyro': (0.001, 0.002, -0.002),
    'euler': (0.0, 1.0, 90.0),
    'quaternion': (0.7, -0.7, 0.0, 0.0),
    'linear_acceleration': (0.01, 0.02, 0.03),
    'gravity': (0.1, -9.8, -1.0),
}


class TestBNO055Init(unittest.TestCase):

    def test_init_defaults(self):
        sensor = make_sensor()
        self.assertEqual(sensor.name, 'bno055')
        self.assertEqual(sensor.address, 0x28)
        self.assertEqual(sensor.line_offset, 0)
        self.assertFalse(sensor.test_on_boot)
        self.assertIsNone(sensor.data)
        self.assertEqual(sensor.last_val, 0xFFFF)
        mock_board.I2C.assert_called_once()
        mock_adafruit_bno055.BNO055_I2C.assert_called_once_with(
            mock_board.I2C.return_value, address=0x28
        )

    def test_init_custom_params(self):
        sensor = make_sensor(name='myimu', address=0x29, line_offset=2)
        self.assertEqual(sensor.name, 'myimu')
        self.assertEqual(sensor.address, 0x29)
        self.assertEqual(sensor.line_offset, 2)
        mock_adafruit_bno055.BNO055_I2C.assert_called_once_with(
            mock_board.I2C.return_value, address=0x29
        )

    def test_init_raises_on_sensor_error(self):
        mock_board.I2C.side_effect = Exception("I2C not found")
        with self.assertRaises(RuntimeError) as ctx:
            BNO055()
        self.assertIn("Error initializing sensor", str(ctx.exception))
        mock_board.I2C.side_effect = None  # reset

    def test_init_test_on_boot(self):
        # test_on_boot=True triggers read_data in a loop; patch read_data and time.sleep
        # to break out after one iteration
        call_count = {'n': 0}

        def fake_read_data(self_inner):
            call_count['n'] += 1

        with patch('modules.sensor.imu.bno055.bno055.time.sleep', side_effect=StopIteration), \
             patch.object(BNO055, 'read_data', fake_read_data):
            with self.assertRaises(StopIteration):
                make_sensor(test_on_boot=True)

        self.assertEqual(call_count['n'], 1)


class TestBNO055GetEuler(unittest.TestCase):

    def setUp(self):
        self.sensor = make_sensor()
        self.sensor.sensor.euler = (10.0, 2.0, 45.0)

    def test_get_euler(self):
        result = self.sensor.get_euler()
        self.assertEqual(result, (10.0, 2.0, 45.0))


class TestBNO055GetData(unittest.TestCase):

    def setUp(self):
        self.sensor = make_sensor()
        mock_hw = self.sensor.sensor
        mock_hw.temperature = SAMPLE_DATA['temperature']
        mock_hw.acceleration = SAMPLE_DATA['acceleration']
        mock_hw.magnetic = SAMPLE_DATA['magnetic']
        mock_hw.gyro = SAMPLE_DATA['gyro']
        mock_hw.euler = SAMPLE_DATA['euler']
        mock_hw.quaternion = SAMPLE_DATA['quaternion']
        mock_hw.linear_acceleration = SAMPLE_DATA['linear_acceleration']
        mock_hw.gravity = SAMPLE_DATA['gravity']

    def test_get_data_returns_all_fields(self):
        data = self.sensor._get_data()
        self.assertEqual(set(data.keys()), {
            'temperature', 'acceleration', 'magnetic', 'gyro',
            'euler', 'quaternion', 'linear_acceleration', 'gravity'
        })
        self.assertEqual(data['temperature'], SAMPLE_DATA['temperature'])
        self.assertEqual(data['acceleration'], SAMPLE_DATA['acceleration'])
        self.assertEqual(data['euler'], SAMPLE_DATA['euler'])


class TestBNO055PublishChangedData(unittest.TestCase):

    def _setup_sensor_with_data(self, data_override=None):
        sensor = make_sensor()
        hw = sensor.sensor
        d = SAMPLE_DATA.copy()
        if data_override:
            d.update(data_override)
        hw.temperature = d['temperature']
        hw.acceleration = d['acceleration']
        hw.magnetic = d['magnetic']
        hw.gyro = d['gyro']
        hw.euler = d['euler']
        hw.quaternion = d['quaternion']
        hw.linear_acceleration = d['linear_acceleration']
        hw.gravity = d['gravity']
        mock_ms = MagicMock()
        sensor.messaging_service = mock_ms
        return sensor, mock_ms

    def test_initial_publish(self):
        sensor, mock_ms = self._setup_sensor_with_data()
        self.assertIsNone(sensor.data)
        expected_data = sensor._get_data()
        result = sensor.publish_changed_data()
        self.assertTrue(result)
        mock_ms.publish.assert_called_once_with(
            f'imu/{sensor.name}/data', data=expected_data
        )
        self.assertIsNotNone(sensor.data)

    def test_no_change_below_threshold(self):
        sensor, mock_ms = self._setup_sensor_with_data()
        # Prime with initial data
        sensor.publish_changed_data()
        mock_ms.reset_mock()

        # Data unchanged — second call should return False and not publish
        result = sensor.publish_changed_data()
        self.assertFalse(result)
        mock_ms.publish.assert_not_called()

    def test_scalar_change_exceeds_threshold(self):
        sensor, mock_ms = self._setup_sensor_with_data()
        sensor.publish_changed_data()
        mock_ms.reset_mock()

        # Change temperature by more than threshold (0.5); implementation publishes only changed key
        new_temp = SAMPLE_DATA['temperature'] + 1.0
        sensor.sensor.temperature = new_temp
        result = sensor.publish_changed_data()
        self.assertTrue(result)
        # Only the changed key/value is published (not the full data dict)
        mock_ms.publish.assert_called_once_with(
            f'imu/{sensor.name}/data',
            data={'temperature': new_temp}
        )

    def test_scalar_change_below_threshold_no_publish(self):
        sensor, mock_ms = self._setup_sensor_with_data()
        sensor.publish_changed_data()
        mock_ms.reset_mock()

        # Change temperature by less than threshold (0.5)
        sensor.sensor.temperature = SAMPLE_DATA['temperature'] + 0.1
        result = sensor.publish_changed_data()
        self.assertFalse(result)
        mock_ms.publish.assert_not_called()

    def test_tuple_change_exceeds_threshold(self):
        sensor, mock_ms = self._setup_sensor_with_data()
        sensor.publish_changed_data()
        mock_ms.reset_mock()

        # Change acceleration by more than threshold (0.3)
        new_acc = (SAMPLE_DATA['acceleration'][0] + 1.0,
                   SAMPLE_DATA['acceleration'][1],
                   SAMPLE_DATA['acceleration'][2])
        sensor.sensor.acceleration = new_acc
        result = sensor.publish_changed_data()
        self.assertTrue(result)
        mock_ms.publish.assert_called_once_with(
            f'imu/{sensor.name}/data',
            data={'acceleration': new_acc}
        )

    def test_euler_change_publishes_and_prints_pitch(self):
        sensor, mock_ms = self._setup_sensor_with_data()
        sensor.publish_changed_data()
        mock_ms.reset_mock()

        # Change euler by more than threshold (1.0)
        new_euler = (0.0, 5.0, 90.0)  # pitch changes from 1.0 to 5.0
        sensor.sensor.euler = new_euler
        with patch('builtins.print') as mock_print:
            result = sensor.publish_changed_data()
        self.assertTrue(result)
        # Verify pitch was printed
        mock_print.assert_called_with(f"S:{new_euler[1]}")
        mock_ms.publish.assert_called_once_with(
            f'imu/{sensor.name}/data',
            data={'euler': new_euler}
        )

    def test_non_numeric_change_falls_back_to_inequality(self):
        sensor, mock_ms = self._setup_sensor_with_data()
        sensor.publish_changed_data()
        mock_ms.reset_mock()

        # Simulate a non-numeric value that can't be subtracted
        sensor.data['temperature'] = 'unknown'
        sensor.sensor.temperature = 25
        result = sensor.publish_changed_data()
        self.assertTrue(result)

    def test_returns_false_when_no_data_change(self):
        sensor, mock_ms = self._setup_sensor_with_data()
        sensor.publish_changed_data()
        mock_ms.reset_mock()

        result = sensor.publish_changed_data()
        self.assertFalse(result)


class TestBNO055ReadData(unittest.TestCase):

    def test_read_data_prints_all_fields(self):
        sensor = make_sensor(name='test_imu')
        hw = sensor.sensor
        hw.temperature = 22
        hw.acceleration = (0.0, 0.0, 9.8)
        hw.magnetic = (1.0, 2.0, 3.0)
        hw.gyro = (0.0, 0.0, 0.0)
        hw.euler = (90.0, 0.0, 0.0)
        hw.quaternion = (1.0, 0.0, 0.0, 0.0)
        hw.linear_acceleration = (0.0, 0.0, 0.0)
        hw.gravity = (0.0, 0.0, 9.8)

        with patch('builtins.print') as mock_print:
            sensor.read_data()

        printed = [str(c) for c in mock_print.call_args_list]
        full_output = ' '.join(printed)
        self.assertIn('test_imu', full_output)
        self.assertIn('Temperature', full_output)
        self.assertIn('Accelerometer', full_output)
        self.assertIn('Magnetometer', full_output)
        self.assertIn('Gyroscope', full_output)
        self.assertIn('Euler', full_output)
        self.assertIn('Quaternion', full_output)
        self.assertIn('Linear acceleration', full_output)
        self.assertIn('Gravity', full_output)


if __name__ == '__main__':
    unittest.main()

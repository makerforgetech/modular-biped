import collections
import time
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, call


def _make_servo(model='ST', speed=300, acceleration=50, range=(0, 4095)):
    """
    Build a Servo instance with all hardware dependencies mocked out.
    The messaging service is wired up so subscribe/publish work via simple
    dict-based stubs (avoiding the real pub/sub library).
    """
    from modules.actuators.bus_servo import bus_servo as servo_mod

    # Create a mock backend servo (replaces WaveshareBusServo, etc.)
    mock_backend = MagicMock()
    mock_backend.get_moving.return_value = 0
    mock_backend.get_position.return_value = 100

    # Patch BusServoFactory.create so no hardware SDK is imported
    with patch.object(servo_mod.BusServoFactory, 'create', return_value=mock_backend):
        kwargs = {
            'name': 'test_servo',
            'model': model,
            'id': 1,
            'range': list(range),
            'speed': speed,
            'acceleration': acceleration,
            'baudrate': 1000000,
            'port': '/dev/ttyAMA0',
            'calibrate_on_boot': False,
            'demonstrate_on_boot': False,
            'center_on_boot': False,
            'start': None,
            'poses': [],
        }
        sv = servo_mod.Servo(**kwargs)

    sv.pos = 100  # Set a known current position

    # Wire up a mock messaging service
    messaging_service = MagicMock()
    sv._messaging_service = messaging_service

    return sv, mock_backend


class TestBusServoQueue(unittest.TestCase):

    def setUp(self):
        self.sv, self.ph = _make_servo()

    # ------------------------------------------------------------------
    # move (queues the request)
    # ------------------------------------------------------------------
    def test_queue_move_adds_item(self):
        self.sv.move(500)
        self.assertEqual(len(self.sv._move_queue), 1)
        item = self.sv._move_queue[0]
        self.assertEqual(item['position'], 500)
        self.assertEqual(item['speed'], self.sv.speed)
        self.assertEqual(item['acceleration'], self.sv.acceleration)
        self.assertEqual(item['delay'], 0)
        self.assertAlmostEqual(item['timestamp'], time.time(), delta=1.0)

    def test_queue_move_speed_acceleration_override(self):
        self.sv.move(200, speed=100, acceleration=10)
        item = self.sv._move_queue[0]
        self.assertEqual(item['speed'], 100)
        self.assertEqual(item['acceleration'], 10)

    def test_queue_move_delay_stored(self):
        self.sv.move(300, delay=2.5)
        item = self.sv._move_queue[0]
        self.assertEqual(item['delay'], 2.5)

    def test_queue_move_multiple_items(self):
        self.sv.move(100)
        self.sv.move(200)
        self.sv.move(300)
        self.assertEqual(len(self.sv._move_queue), 3)
        positions = [item['position'] for item in self.sv._move_queue]
        self.assertEqual(positions, [100, 200, 300])

    # ------------------------------------------------------------------
    # _process_queue
    # ------------------------------------------------------------------
    def test_process_queue_empty_does_nothing(self):
        self.sv._do_move = MagicMock()
        self.sv._process_queue()
        self.sv._do_move.assert_not_called()

    def test_process_queue_calls_move_when_idle(self):
        self.sv.is_moving = MagicMock(return_value=False)
        self.sv._do_move = MagicMock()
        self.sv.move(500)
        self.sv._process_queue()
        self.sv._do_move.assert_called_once_with(500, self.sv.speed, self.sv.acceleration)
        self.assertEqual(len(self.sv._move_queue), 0)

    def test_process_queue_does_not_move_while_moving(self):
        self.sv.is_moving = MagicMock(return_value=True)
        self.sv._do_move = MagicMock()
        self.sv.move(500)
        self.sv._process_queue()
        self.sv._do_move.assert_not_called()
        self.assertEqual(len(self.sv._move_queue), 1)

    def test_process_queue_respects_delay(self):
        self.sv.is_moving = MagicMock(return_value=False)
        self.sv._do_move = MagicMock()
        # Add item with a future delay
        self.sv.move(500, delay=100)
        self.sv._process_queue()
        # Should NOT move yet because delay has not elapsed
        self.sv._do_move.assert_not_called()
        self.assertEqual(len(self.sv._move_queue), 1)

    def test_process_queue_executes_after_delay_elapsed(self):
        self.sv.is_moving = MagicMock(return_value=False)
        self.sv._do_move = MagicMock()
        self.sv.move(500, delay=0)
        # Backdate the timestamp to simulate delay already elapsed
        self.sv._move_queue[0]['timestamp'] = time.time() - 5
        self.sv._process_queue()
        self.sv._do_move.assert_called_once()

    def test_process_queue_processes_one_item_per_call(self):
        self.sv.is_moving = MagicMock(return_value=False)
        self.sv._do_move = MagicMock()
        self.sv.move(100)
        self.sv.move(200)
        self.sv._process_queue()
        # Only first item should be processed
        self.assertEqual(len(self.sv._move_queue), 1)
        self.sv._do_move.assert_called_once_with(100, self.sv.speed, self.sv.acceleration)

    def test_process_queue_uses_per_item_speed_acceleration(self):
        self.sv.is_moving = MagicMock(return_value=False)
        self.sv._do_move = MagicMock()
        self.sv.move(400, speed=50, acceleration=5)
        self.sv._process_queue()
        self.sv._do_move.assert_called_once_with(400, 50, 5)

    # ------------------------------------------------------------------
    # _do_move – no blocking sleep, delegates to backend
    # ------------------------------------------------------------------
    def test_move_does_not_block(self):
        """_do_move() must not call time.sleep (blocking removed)."""
        with patch('time.sleep') as mock_sleep:
            self.sv._do_move(500)
        mock_sleep.assert_not_called()

    def test_move_accepts_speed_acceleration_params(self):
        """_do_move() should delegate the move to the backend servo."""
        self.sv._do_move(500, speed=10, acceleration=2)
        self.ph.move_to.assert_called_once_with(500, unit='degrees')

    def test_move_uses_instance_defaults_when_not_supplied(self):
        self.sv._do_move(500)
        self.ph.move_to.assert_called_once_with(500, unit='degrees')

    # ------------------------------------------------------------------
    # setup_messaging subscriptions
    # ------------------------------------------------------------------
    def test_loop_calls_process_queue(self):
        """loop() should call _process_queue to drain the move queue."""
        with patch.object(self.sv, '_process_queue') as mock_pq:
            self.sv.loop()
            mock_pq.assert_called_once()

    def test_setup_messaging_does_not_subscribe_to_system_loop(self):
        """system/loop subscription replaced by direct loop() call — should not be in subscriptions."""
        messaging_service = MagicMock()
        with patch.object(self.sv, 'get_position', return_value=100):
            self.sv.messaging_service = messaging_service

        topics = [c.args[0] for c in messaging_service.subscribe.call_args_list]
        self.assertNotIn('system/loop', topics)

    def test_setup_messaging_subscribes_queue_topic(self):
        messaging_service = MagicMock()
        with patch.object(self.sv, 'get_position', return_value=100):
            self.sv.messaging_service = messaging_service

        topics = [c.args[0] for c in messaging_service.subscribe.call_args_list]
        self.assertIn('servo:test_servo:queue', topics)

    def test_setup_messaging_mvabs_uses_queue_move(self):
        messaging_service = MagicMock()
        with patch.object(self.sv, 'get_position', return_value=100):
            self.sv.messaging_service = messaging_service

        # Find the callback registered for ':mvabs'
        subscriptions = {c.args[0]: c.args[1] for c in messaging_service.subscribe.call_args_list}
        self.assertIn('servo:test_servo:mvabs', subscriptions)
        self.assertEqual(subscriptions['servo:test_servo:mvabs'], self.sv.move)


if __name__ == '__main__':
    unittest.main()

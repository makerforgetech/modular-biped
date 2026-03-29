import collections
import time
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, call


def _make_manager(model='ST', speed=300, acceleration=50, range=(0, 4095)):
    """
    Build a ServoManager with a single servo and all hardware dependencies
    mocked out.  Returns (manager, servo_state, mock_backend).
    """
    from modules.actuators.bus_servo import bus_servo as servo_mod

    mock_backend = MagicMock()
    mock_backend.get_moving.return_value = 0
    mock_backend.get_position.return_value = 100

    servo_cfg = {
        'name': 'test_servo',
        'model': model,
        'id': 1,
        'range': list(range),
        'speed': speed,
        'acceleration': acceleration,
        'baudrate': 1000000,
        'port': '/dev/ttyAMA0',
        'start': None,
    }

    with patch.object(servo_mod.BusServoFactory, 'create', return_value=mock_backend):
        manager = servo_mod.ServoManager(
            backend='simulation',
            servos=[servo_cfg],
        )

    servo_state = manager._servos['test_servo']
    servo_state.pos = 100  # Set a known current position

    # Wire up a mock messaging service
    messaging_service = MagicMock()
    manager._messaging_service = messaging_service

    return manager, servo_state, mock_backend


class TestServoManagerQueue(unittest.TestCase):

    def setUp(self):
        self.manager, self.servo_state, self.mock_backend = _make_manager()

    # ------------------------------------------------------------------
    # move (queues the request)
    # ------------------------------------------------------------------
    def test_queue_move_adds_item(self):
        self.servo_state.move(500)
        self.assertEqual(len(self.servo_state._move_queue), 1)
        item = self.servo_state._move_queue[0]
        self.assertEqual(item['position'], 500)
        self.assertEqual(item['speed'], self.servo_state.speed)
        self.assertEqual(item['acceleration'], self.servo_state.acceleration)
        self.assertEqual(item['delay'], 0)
        self.assertAlmostEqual(item['timestamp'], time.time(), delta=1.0)

    def test_queue_move_speed_acceleration_override(self):
        self.servo_state.move(200, speed=100, acceleration=10)
        item = self.servo_state._move_queue[0]
        self.assertEqual(item['speed'], 100)
        self.assertEqual(item['acceleration'], 10)

    def test_queue_move_delay_stored(self):
        self.servo_state.move(300, delay=2.5)
        item = self.servo_state._move_queue[0]
        self.assertEqual(item['delay'], 2.5)

    def test_queue_move_multiple_items(self):
        self.servo_state.move(100)
        self.servo_state.move(200)
        self.servo_state.move(300)
        self.assertEqual(len(self.servo_state._move_queue), 3)
        positions = [item['position'] for item in self.servo_state._move_queue]
        self.assertEqual(positions, [100, 200, 300])

    # ------------------------------------------------------------------
    # _process_servo_queue
    # ------------------------------------------------------------------
    def test_process_queue_empty_does_nothing(self):
        self.manager._do_move = MagicMock()
        self.manager._process_servo_queue(self.servo_state)
        self.manager._do_move.assert_not_called()

    def test_process_queue_calls_move_when_idle(self):
        self.manager.is_servo_moving = MagicMock(return_value=False)
        self.manager._do_move = MagicMock()
        self.servo_state.move(500)
        self.manager._process_servo_queue(self.servo_state)
        self.manager._do_move.assert_called_once_with(
            self.servo_state, 500,
            self.servo_state.speed, self.servo_state.acceleration,
        )
        self.assertEqual(len(self.servo_state._move_queue), 0)

    def test_process_queue_does_not_move_while_moving(self):
        self.manager.is_servo_moving = MagicMock(return_value=True)
        self.manager._do_move = MagicMock()
        self.servo_state.move(500)
        self.manager._process_servo_queue(self.servo_state)
        self.manager._do_move.assert_not_called()
        self.assertEqual(len(self.servo_state._move_queue), 1)

    def test_process_queue_respects_delay(self):
        self.manager.is_servo_moving = MagicMock(return_value=False)
        self.manager._do_move = MagicMock()
        self.servo_state.move(500, delay=100)
        self.manager._process_servo_queue(self.servo_state)
        self.manager._do_move.assert_not_called()
        self.assertEqual(len(self.servo_state._move_queue), 1)

    def test_process_queue_executes_after_delay_elapsed(self):
        self.manager.is_servo_moving = MagicMock(return_value=False)
        self.manager._do_move = MagicMock()
        self.servo_state.move(500, delay=0)
        self.servo_state._move_queue[0]['timestamp'] = time.time() - 5
        self.manager._process_servo_queue(self.servo_state)
        self.manager._do_move.assert_called_once()

    def test_process_queue_processes_one_item_per_call(self):
        self.manager.is_servo_moving = MagicMock(return_value=False)
        self.manager._do_move = MagicMock()
        self.servo_state.move(100)
        self.servo_state.move(200)
        self.manager._process_servo_queue(self.servo_state)
        self.assertEqual(len(self.servo_state._move_queue), 1)
        self.manager._do_move.assert_called_once_with(
            self.servo_state, 100,
            self.servo_state.speed, self.servo_state.acceleration,
        )

    def test_process_queue_uses_per_item_speed_acceleration(self):
        self.manager.is_servo_moving = MagicMock(return_value=False)
        self.manager._do_move = MagicMock()
        self.servo_state.move(400, speed=50, acceleration=5)
        self.manager._process_servo_queue(self.servo_state)
        self.manager._do_move.assert_called_once_with(self.servo_state, 400, 50, 5)

    # ------------------------------------------------------------------
    # _do_move – no blocking sleep, delegates to backend
    # ------------------------------------------------------------------
    def test_move_does_not_block(self):
        """_do_move() must not call time.sleep."""
        with patch('time.sleep') as mock_sleep:
            self.manager._do_move(self.servo_state, 500)
        mock_sleep.assert_not_called()

    def test_move_accepts_speed_acceleration_params(self):
        """_do_move() should delegate the move to the backend."""
        self.manager._do_move(self.servo_state, 500, speed=10, acceleration=2)
        self.mock_backend.move_to.assert_called_once_with(500, unit='degrees')

    def test_move_uses_backend_when_not_supplied(self):
        self.manager._do_move(self.servo_state, 500)
        self.mock_backend.move_to.assert_called_once_with(500, unit='degrees')

    # ------------------------------------------------------------------
    # loop()
    # ------------------------------------------------------------------
    def test_loop_processes_all_servos(self):
        """loop() should call _process_servo_queue for every managed servo."""
        with patch.object(self.manager, '_process_servo_queue') as mock_pq:
            self.manager.loop()
            mock_pq.assert_called_once_with(self.servo_state)

    # ------------------------------------------------------------------
    # setup_messaging subscriptions
    # ------------------------------------------------------------------
    def test_setup_messaging_subscribes_queue_topic(self):
        messaging_service = MagicMock()
        with patch.object(self.manager, 'get_servo_position', return_value=100):
            self.manager.messaging_service = messaging_service

        topics = [c.args[0] for c in messaging_service.subscribe.call_args_list]
        self.assertIn('servo:test_servo:queue', topics)

    def test_setup_messaging_mvabs_uses_queue_move(self):
        messaging_service = MagicMock()
        with patch.object(self.manager, 'get_servo_position', return_value=100):
            self.manager.messaging_service = messaging_service

        subscriptions = {c.args[0]: c.args[1] for c in messaging_service.subscribe.call_args_list}
        self.assertIn('servo:test_servo:mvabs', subscriptions)
        self.assertEqual(subscriptions['servo:test_servo:mvabs'], self.servo_state.move)

    # ------------------------------------------------------------------
    # Dict-like interface
    # ------------------------------------------------------------------
    def test_getitem_returns_servo_state(self):
        from modules.actuators.bus_servo.bus_servo import ServoState
        self.assertIsInstance(self.manager['test_servo'], ServoState)

    def test_iter_yields_servo_names(self):
        self.assertIn('test_servo', list(self.manager))

    def test_contains_servo_name(self):
        self.assertIn('test_servo', self.manager)

    def test_items_returns_name_state_pairs(self):
        items = dict(self.manager.items())
        self.assertIn('test_servo', items)

    # ------------------------------------------------------------------
    # Group move / pose
    # ------------------------------------------------------------------
    def test_group_move_queues_for_all_servos(self):
        self.servo_state.move = MagicMock()
        self.manager.group_move({'test_servo': 200})
        self.servo_state.move.assert_called_once_with(200)

    def test_move_to_pose_unknown_logs_warning(self):
        self.manager.log = MagicMock()
        self.manager.move_to_pose('nonexistent_pose')
        self.manager.log.assert_called_once()

    def test_move_to_pose_known_queues_moves(self):
        self.manager._poses = {'test_pose': {'test_servo': 150}}
        self.servo_state.move = MagicMock()
        self.manager.move_to_pose('test_pose')
        self.servo_state.move.assert_called_once_with(150)

    # ------------------------------------------------------------------
    # ServoState delegates to manager
    # ------------------------------------------------------------------
    def test_servo_state_detach_delegates(self):
        self.manager.detach_servo = MagicMock()
        self.servo_state.detach()
        self.manager.detach_servo.assert_called_once_with('test_servo')

    def test_servo_state_attach_delegates(self):
        self.manager.attach_servo = MagicMock()
        self.servo_state.attach()
        self.manager.attach_servo.assert_called_once_with('test_servo')

    def test_servo_state_get_position_delegates(self):
        self.manager.get_servo_position = MagicMock(return_value=42.0)
        pos = self.servo_state.get_position()
        self.assertEqual(pos, 42.0)

    def test_servo_state_is_moving_delegates(self):
        self.manager.is_servo_moving = MagicMock(return_value=True)
        self.assertTrue(self.servo_state.is_moving())

    def test_servo_state_move_relative_clamps_to_range(self):
        self.servo_state.pos = 100
        self.servo_state.range = [0, 110]
        self.servo_state.move = MagicMock()
        self.servo_state.move_relative(50)  # would reach 150, clamps to 110
        self.servo_state.move.assert_called_once_with(110)


if __name__ == '__main__':
    unittest.main()

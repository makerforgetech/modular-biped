import sys
import unittest
from unittest.mock import MagicMock, patch
from modules.actuators.bus_servo.libraries.simulation_backend import SimulationBusServo
from modules.actuators.bus_servo.libraries.factory import BusServoFactory
from modules.actuators.bus_servo.libraries.waveshare_backend import WaveshareBusServo


class TestWaveshareBusServo(unittest.TestCase):
    def setUp(self):
        # Mock the dynamic import of STservo_sdk
        sys.modules['numpy'] = MagicMock()
        self.mock_packet = MagicMock()
        mock_sts = MagicMock(return_value=self.mock_packet)
        mock_PortHandler = MagicMock()
        sys.modules['modules.actuators.bus_servo.libraries.waveshare.STservo_sdk'] = MagicMock(
            sts=mock_sts,
            PortHandler=mock_PortHandler
        )
        # Clear any cached port singletons from previous tests
        WaveshareBusServo._port_singletons.clear()
        self.servo = WaveshareBusServo(1, 'ST3215', '/dev/ttyUSB0', range=[0, 180])
        self.servo.packetHandler = self.mock_packet
        self.servo.portHandler = MagicMock()
        self.servo.speed = 10
        self.servo.acceleration = 5
        self.servo.range = [0, 180]
        self.servo.log = MagicMock()
        # Set up default return values for SDK methods that return (comm_result, error) tuples
        self.mock_packet.WritePosEx.return_value = (0, 0)
        self.mock_packet.WheelMode.return_value = (0, 0)
        self.mock_packet.WriteSpec.return_value = (0, 0)

    def tearDown(self):
        sys.modules.pop('modules.actuators.bus_servo.libraries.waveshare.STservo_sdk', None)
        sys.modules.pop('numpy', None)
        WaveshareBusServo._port_singletons.clear()

    def test_move_to(self):
        self.servo.move_to(90, unit='degrees')
        self.servo.move_to(1.57, unit='radians')
        self.servo.move_to(2048, unit='raw')

    def test_get_position(self):
        self.servo.get_position_raw = MagicMock(return_value=2048)
        pos_deg = self.servo.get_position(unit='degrees')
        pos_rad = self.servo.get_position(unit='radians')
        pos_raw = self.servo.get_position(unit='raw')
        self.assertIsInstance(pos_deg, float)
        self.assertIsInstance(pos_rad, float)
        self.assertEqual(pos_raw, 2048)

    def test_set_speed(self):
        self.servo.set_speed(20, unit='degrees')

    def test_attach_detach(self):
        self.servo.attach()
        self.servo.detach()

    def test_exit_decrements_refcount(self):
        # After __init__ the refcount should be 1 in the singleton
        model_type = 'ST'
        key = (self.servo.port, self.servo.baudrate, model_type)
        # Patch portHandler.closePort so it doesn't error
        self.servo.portHandler.closePort = MagicMock()
        initial_refcount = WaveshareBusServo._port_singletons.get(key, {}).get('refcount', 0)
        self.servo.exit()
        # Either the key is removed (refcount hit 0) or refcount decreased
        if key in WaveshareBusServo._port_singletons:
            self.assertLess(WaveshareBusServo._port_singletons[key]['refcount'], initial_refcount)
        # No exception = pass

    def test_move_to_raw(self):
        self.servo.move_to_raw(1234)

    def test_get_speed(self):
        self.mock_packet.ReadPosSpeed.return_value = (0, 10, 0, 0)
        self.servo.model = 'ST3215'
        self.servo.handle_errors = MagicMock(return_value=False)
        speed = self.servo.get_speed()
        self.assertEqual(speed, 10)

    def test_get_moving(self):
        self.mock_packet.ReadMoving.return_value = (1, 0, 0)
        self.servo.model = 'ST3215'
        self.servo.handle_errors = MagicMock(return_value=False)
        moving = self.servo.get_moving()
        self.assertEqual(moving, 1)

    def test_enable_continuous(self):
        self.mock_packet.WheelMode.return_value = (0, 0)
        self.servo.model = 'ST3215'
        self.servo.handle_errors = MagicMock(return_value=False)
        self.servo.enable_continuous()

    def test_turn_wheel(self):
        self.mock_packet.WriteSpec.return_value = (0, 0)
        self.servo.model = 'ST3215'
        self.servo.handle_errors = MagicMock(return_value=False)
        self.servo.turn_wheel(50)

    def test_handle_errors(self):
        self.servo.packetHandler.getTxRxResult = MagicMock(return_value='err')
        self.servo.packetHandler.getRxPacketError = MagicMock(return_value='err')
        self.servo.log = MagicMock()
        import sys
        sys.modules['modules.actuators.bus_servo.libraries.waveshare_backend'].COMM_SUCCESS = 0
        self.assertTrue(self.servo.handle_errors(1, 0))
        self.assertTrue(self.servo.handle_errors(0, 1))
        self.assertFalse(self.servo.handle_errors(0, 0))

    def test_calibrate_to_center(self):
        self.servo.handle_errors = MagicMock(return_value=False)
        self.servo.range = [0, 180]
        self.servo.model = 'ST3215'
        self.servo.calibrate_to_center()

    def test_shared_port_singleton(self):
        """Two servos on the same port/baudrate/model share one portHandler."""
        # First servo was created in setUp.  Create a second on the same bus.
        second = WaveshareBusServo(2, 'ST3215', '/dev/ttyUSB0', range=[0, 180])
        key = ('/dev/ttyUSB0', 1000000, 'ST')
        singleton_port = WaveshareBusServo._port_singletons[key]['portHandler']
        # Both instances must use the singleton's portHandler (not distinct ones)
        self.assertIs(second.portHandler, singleton_port)
        self.assertEqual(WaveshareBusServo._port_singletons[key]['refcount'], 2)


class TestRustypotBusServo(unittest.TestCase):
    def setUp(self):
        # Mock numpy with real ndarray type so isinstance checks work
        import types
        mock_np = MagicMock()
        mock_np.deg2rad = lambda x: x
        mock_np.rad2deg = lambda x: x
        # Make ndarray a real type so isinstance(rad, np.ndarray) doesn't raise
        mock_np.ndarray = type('ndarray', (), {})
        sys.modules['numpy'] = mock_np

        self.mock_controller = MagicMock()
        mock_rustypot = MagicMock()
        mock_rustypot.Sts3215PyController.return_value = self.mock_controller
        mock_rustypot.Scs0009PyController.return_value = self.mock_controller
        sys.modules['rustypot'] = mock_rustypot
        from modules.actuators.bus_servo.libraries.rustypot_backend import RustypotBusServo
        self.servo = RustypotBusServo(1, 'ST3215', '/dev/ttyUSB0', range=[0, 180])
        self.servo.controller = self.mock_controller

    def tearDown(self):
        sys.modules.pop('rustypot', None)
        sys.modules.pop('numpy', None)

    def test_move_to(self):
        self.servo.move_to(90, unit='degrees')
        self.servo.move_to(1.57, unit='radians')
        self.servo.move_to(1.0, unit='raw')
        self.mock_controller.write_goal_position.assert_called()

    def test_get_position(self):
        self.mock_controller.read_present_position.return_value = 1.57
        pos_deg = self.servo.get_position(unit='degrees')
        pos_rad = self.servo.get_position(unit='radians')
        pos_raw = self.servo.get_position(unit='raw')
        self.assertIsInstance(pos_deg, float)
        self.assertEqual(pos_rad, 1.57)
        self.assertEqual(pos_raw, 1.57)

    def test_set_speed(self):
        self.servo.set_speed(20, unit='degrees')

    def test_attach_detach(self):
        self.servo.attach()
        self.servo.detach()
        self.mock_controller.write_torque_enable.assert_called()

    def test_exit(self):
        self.servo.exit()
        self.mock_controller.write_torque_enable.assert_called_with(1, False)

    def test_move_to_raw(self):
        self.servo.move_to_raw(1.23)
        self.mock_controller.write_goal_position.assert_called_with(1, 1.23)

    def test_get_position_raw(self):
        self.mock_controller.read_present_position.return_value = 1.23
        self.assertEqual(self.servo.get_position_raw(), 1.23)

    def test_get_speed(self):
        self.mock_controller.read_present_speed.return_value = 1.0
        speed = self.servo.get_speed(unit='degrees')
        self.assertIsInstance(speed, float)

    def test_get_moving(self):
        self.mock_controller.read_present_speed.return_value = 0.0
        self.assertFalse(self.servo.get_moving())
        self.mock_controller.read_present_speed.return_value = 1.0
        self.assertTrue(self.servo.get_moving())

    def test_enable_continuous(self):
        with self.assertRaises(NotImplementedError):
            self.servo.enable_continuous()

    def test_turn_wheel(self):
        with self.assertRaises(NotImplementedError):
            self.servo.turn_wheel(10)

    def test_handle_errors(self):
        self.assertFalse(self.servo.handle_errors(0, 0))

    def test_calibrate_to_center(self):
        self.servo.move_to = MagicMock()
        self.servo.range = [0, 180]
        self.servo.calibrate_to_center()
        self.servo.move_to.assert_called()


class TestServoManager(unittest.TestCase):
    def _make_manager(self, **extra_cfg):
        from modules.actuators.bus_servo.bus_servo import ServoManager, ServoState

        mock_backend = MagicMock()
        mock_backend.get_moving.return_value = 0
        mock_backend.get_position.return_value = 90.0

        servo_cfg = {
            'name': 'test',
            'id': 1,
            'range': [0, 180],
            'model': 'ST3215',
            **extra_cfg,
        }

        with patch.object(BusServoFactory, 'create', return_value=mock_backend):
            mgr = ServoManager(backend='simulation', servos=[servo_cfg])

        return mgr, mgr._servos['test'], mock_backend

    def test_init_creates_servo_state(self):
        from modules.actuators.bus_servo.bus_servo import ServoState
        mgr, sv, _ = self._make_manager()
        self.assertIsInstance(sv, ServoState)
        self.assertEqual(sv.identifier, 'test')
        self.assertEqual(sv.range, [0, 180])

    def test_init_simulation_backend(self):
        sim = BusServoFactory.create(
            backend='simulation', model='ST3215', servo_id=1, port='sim', range=[0, 180]
        )
        self.assertIsInstance(sim, SimulationBusServo)

    def test_do_move_calls_backend(self):
        mgr, sv, backend = self._make_manager()
        sv.pos = 90
        mgr._do_move(sv, 90)
        backend.move_to.assert_called_once_with(90, unit='degrees')
        self.assertEqual(sv.pos, 90)

    def test_do_move_out_of_range_logs_error(self):
        mgr, sv, backend = self._make_manager()
        mgr.log = MagicMock()
        mgr._do_move(sv, 999)
        backend.move_to.assert_not_called()
        mgr.log.assert_called_once()

    def test_get_servo_position(self):
        mgr, sv, backend = self._make_manager()
        backend.get_position.return_value = 45.0
        pos = mgr.get_servo_position('test')
        self.assertEqual(pos, 45.0)
        backend.get_position.assert_called_once_with(unit='degrees')

    def test_detach_servo(self):
        mgr, sv, backend = self._make_manager()
        mgr.detach_servo('test')
        backend.detach.assert_called_once()

    def test_attach_servo(self):
        mgr, sv, backend = self._make_manager()
        mgr.attach_servo('test')
        backend.attach.assert_called_once()

    def test_exit_calls_detach_all_and_backend_exit(self):
        mgr, sv, backend = self._make_manager()
        mgr.exit()
        backend.detach.assert_called()
        backend.exit.assert_called()

    def test_group_move(self):
        mgr, sv, _ = self._make_manager()
        sv.move = MagicMock()
        mgr.group_move({'test': 120})
        sv.move.assert_called_once_with(120)

    def test_move_to_pose(self):
        mgr, sv, _ = self._make_manager()
        mgr._poses = {'stand': {'test': 100}}
        sv.move = MagicMock()
        mgr.move_to_pose('stand')
        sv.move.assert_called_once_with(100)

    def test_dict_like_getitem(self):
        mgr, sv, _ = self._make_manager()
        self.assertIs(mgr['test'], sv)

    def test_dict_like_contains(self):
        mgr, _, _ = self._make_manager()
        self.assertIn('test', mgr)

    def test_dict_like_iter(self):
        mgr, _, _ = self._make_manager()
        self.assertEqual(list(mgr), ['test'])

    def test_dict_like_items(self):
        mgr, sv, _ = self._make_manager()
        self.assertEqual(dict(mgr.items()), {'test': sv})

    def test_simulation_backend_methods(self):
        sim = SimulationBusServo(1, 'ST3215', 'sim', range=[0, 180])
        sim.set_speed(10)
        self.assertEqual(sim.speed, 10)
        sim.detach()
        self.assertFalse(sim.torque_enabled)
        sim.attach()
        self.assertTrue(sim.torque_enabled)
        sim.move_to_raw(100)
        self.assertEqual(sim.position, 100)
        self.assertFalse(sim.get_moving())
        sim.calibrate_to_center()
        self.assertEqual(sim.position, 90)


if __name__ == '__main__':
    unittest.main()

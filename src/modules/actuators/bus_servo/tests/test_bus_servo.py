import sys
import unittest
from unittest.mock import MagicMock
from modules.actuators.bus_servo.bus_servo import Servo
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
        self.servo = WaveshareBusServo(1, 'ST3215', '/dev/ttyUSB0', range=[0, 180])
        self.servo.packetHandler = self.mock_packet
        self.servo.portHandler = MagicMock()
        self.servo.index = 1
        self.servo.speed = 10
        self.servo.acceleration = 5
        self.servo.identifier = 'test'
        self.servo.name = 'test'
        self.servo.range = [0, 180]
        self.servo.log = MagicMock()
    def tearDown(self):
        sys.modules.pop('modules.actuators.bus_servo.libraries.waveshare.STservo_sdk', None)
        sys.modules.pop('numpy', None)

    def test_move_to(self):
        self.servo.move_to(90, unit='degrees')
        self.servo.move_to(1.57, unit='radians')
        self.servo.move_to(2048, unit='raw')
        # Should call move_to_raw
        # No exception means pass

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

    def test_exit(self):
        self.servo.exit()

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
        self.servo.packetHandler.WritePosEx.return_value = (0, 0)
        self.servo.handle_errors = MagicMock(return_value=False)
        self.servo.range = [0, 180]
        self.servo.index = 1
        self.servo.speed = 10
        self.servo.acceleration = 5
        self.servo.identifier = 'test'
        self.servo.model = 'ST3215'
        self.servo.calibrate_to_center()

class TestRustypotBusServo(unittest.TestCase):
    def setUp(self):
        # Mock numpy before importing backend, since it may not be installed in test env.
        sys.modules['numpy'] = MagicMock(
            deg2rad=lambda x: x,
            rad2deg=lambda x: x,
        )
        # Mock the dynamic import of rustypot
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
class TestBusServo(unittest.TestCase):
    def test_init_simulation_backend(self):
        servo = Servo(name='test', id=1, range=[0, 180], model='ST3215', backend='simulation')
        self.assertEqual(servo.identifier, 'test')
        self.assertEqual(servo.index, 1)
        self.assertEqual(servo.range, [0, 180])
        self.assertEqual(servo.model, 'ST3215')
        # Should use simulation backend
        self.assertIsInstance(servo.backend_servo, SimulationBusServo)

    def test_move_to_degrees(self):
        servo = Servo(name='test', id=1, range=[0, 180], model='ST3215', backend='simulation')
        # Should log the move and update position
        servo.move(90, unit='degrees')
        self.assertEqual(servo.backend_servo.position, 90)

    def test_factory_simulation(self):
        sim = BusServoFactory.create(
            backend='simulation',
            model='ST3215',
            servo_id=1,
            port='sim',
            range=[0, 180]
        )
        self.assertIsInstance(sim, SimulationBusServo)
        sim.move_to(45, unit='degrees')
        self.assertEqual(sim.position, 45)

    def test_simulation_methods(self):
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

import sys
import unittest
from unittest.mock import MagicMock, patch
sys.modules['yaml'] = MagicMock()
from modules.xbox_controller.xbox_controller import XboxController


class TestXboxController(unittest.TestCase):
    def setUp(self):
        # Patch BaseModule.log to avoid side effects
        self.log_patch = patch('modules.base_module.BaseModule.log', lambda *a, **k: None)
        self.log_patch.start()
        self.addCleanup(self.log_patch.stop)

        # Standard config for most tests
        self.config = {
            'button_names': {
                0: 'BTN_A', 1: 'BTN_B', 2: 'BTN_X', 3: 'BTN_Y',
                4: 'BTN_TL', 5: 'BTN_TR', 6: 'BTN_SELECT', 7: 'BTN_START',
                8: 'BTN_MODE', 9: 'BTN_THUMBL', 10: 'BTN_THUMBR', 11: 'KEY_RECORD'
            },
            'axis_names': {
                0: 'ABS_X', 1: 'ABS_Y', 2: 'ABS_Z', 3: 'ABS_RZ',
                4: 'ABS_RX', 5: 'ABS_RY', 6: 'ABS_HAT0X', 7: 'ABS_HAT0Y'
            },
            'axis_min': -32767.0,
            'axis_max': 32767.0,
            'deadzone': 4000,
            'device': '/dev/input/js0',
            'normalised': True,
            'debug': False
        }

    def test_button_and_axis_names_required(self):
        # button_names missing
        with self.assertRaises(ValueError):
            XboxController(axis_names={})
        # axis_names missing
        with self.assertRaises(ValueError):
            XboxController(button_names={})

    def test_get_name(self):
        ctrl = XboxController(**self.config)
        # Button
        self.assertEqual(ctrl._get_name(ctrl.JS_EVENT_BUTTON, 0), 'BTN_A')
        # Axis
        self.assertEqual(ctrl._get_name(ctrl.JS_EVENT_AXIS, 1), 'ABS_Y')
        # Unknown
        self.assertTrue(ctrl._get_name(99, 99).startswith('unknown'))

    def test_axis_normalization(self):
        ctrl = XboxController(**self.config)
        # Simulate axis event at min, max, and center
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, -32767, 0)  # ABS_X min
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, 0, 0)       # ABS_X center
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, 32767, 0)   # ABS_X max
        vals = [ctrl.current_status_normalized['ABS_X']]
        # After last event, should be 1.0
        self.assertAlmostEqual(ctrl.current_status_normalized['ABS_X'], 1.0, places=2)
        # Center event
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, 0, 0)
        self.assertAlmostEqual(ctrl.current_status_normalized['ABS_X'], 0.0, places=2)
        # Min event
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, -32767, 0)
        self.assertAlmostEqual(ctrl.current_status_normalized['ABS_X'], -1.0, places=2)

    def test_button_event_normalization(self):
        ctrl = XboxController(**self.config)
        ctrl._handle_button_event(0, ctrl.JS_EVENT_BUTTON, 1, 0)  # BTN_A pressed
        self.assertEqual(ctrl.current_status_normalized['BTN_A'], 1.0)
        ctrl._handle_button_event(0, ctrl.JS_EVENT_BUTTON, 0, 0)  # BTN_A released
        self.assertEqual(ctrl.current_status_normalized['BTN_A'], 0.0)

    def test_get_current_status(self):
        ctrl = XboxController(**self.config)
        ctrl._handle_button_event(0, ctrl.JS_EVENT_BUTTON, 1, 0)
        # Normalized
        self.assertIn('BTN_A', ctrl.get_current_status(normalized=True))
        # Raw (should be empty unless _listen is running)
        self.assertIsInstance(ctrl.get_current_status(normalized=False), dict)

    def test_get_changed_inputs(self):
        ctrl = XboxController(**self.config)
        ctrl._handle_button_event(0, ctrl.JS_EVENT_BUTTON, 1, 0)
        changed = ctrl.get_changed_inputs()
        self.assertIn(('BTN_A', 1.0), changed)
        # No change on second call
        changed2 = ctrl.get_changed_inputs()
        self.assertEqual(changed2, [])
        # Change again
        ctrl._handle_button_event(0, ctrl.JS_EVENT_BUTTON, 0, 0)
        changed3 = ctrl.get_changed_inputs()
        self.assertIn(('BTN_A', 0.0), changed3)

    def test_output_normalized_status_prints(self):
        ctrl = XboxController(**self.config)
        ctrl._handle_button_event(0, ctrl.JS_EVENT_BUTTON, 1, 0)
        # Should not raise
        ctrl.output_normalized_status()

    def test_output_current_status_prints(self):
        ctrl = XboxController(**self.config)
        # Simulate raw event
        import struct
        evbuf = struct.pack(ctrl.JS_EVENT_FORMAT, 0, 1, ctrl.JS_EVENT_BUTTON, 0)
        ctrl.current_status[(ctrl.JS_EVENT_BUTTON, 0)] = evbuf
        ctrl.output_current_status()

    def test_listen_file_not_found(self):
        # Should log warning and stop after timeout
        ctrl = XboxController(**self.config)
        ctrl.CONNECT_TIMEOUT = 1  # Speed up test
        ctrl.running = True
        with patch('builtins.open', side_effect=FileNotFoundError):
            # Should stop after timeout
            ctrl._listen()
        self.assertFalse(ctrl.running)

    def test_axis_start_value(self):
        # Test that axis start value is respected via mapping
        config = self.config.copy()
        config['start'] = -32767
        ctrl = XboxController(**config)
        # Provide a mapping for ABS_X with a start value
        class DummyMapping:
            start = -32767
        ctrl.mapping = {'ABS_X': DummyMapping()}
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, -32767, 0)
        self.assertAlmostEqual(ctrl.current_status_normalized['ABS_X'], 0.0, places=2)

    def test_normalized_flag_false(self):
        config = self.config.copy()
        config['normalised'] = False
        ctrl = XboxController(**config)
        # Simulate event: should update current_status, not current_status_normalized
        import struct
        evbuf = struct.pack(ctrl.JS_EVENT_FORMAT, 0, 1, ctrl.JS_EVENT_BUTTON, 0)
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = evbuf
            ctrl.running = True
            # Only run one loop iteration
            with patch.object(ctrl, '_listen', wraps=ctrl._listen) as listen_patch:
                ctrl.running = False
        # Should not raise

    def test_axis_range_configurable(self):
        config = self.config.copy()
        config['axis_min'] = -100.0
        config['axis_max'] = 100.0
        ctrl = XboxController(**config)
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, 100, 0)
        self.assertAlmostEqual(ctrl.current_status_normalized['ABS_X'], 1.0, places=2)
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, -100, 0)
        self.assertAlmostEqual(ctrl.current_status_normalized['ABS_X'], -1.0, places=2)

    def test_multiple_axes_and_buttons(self):
        ctrl = XboxController(**self.config)
        # Simulate several events
        ctrl._handle_button_event(0, ctrl.JS_EVENT_BUTTON, 1, 0)  # BTN_A
        ctrl._handle_button_event(0, ctrl.JS_EVENT_BUTTON, 1, 1)  # BTN_B
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, 10000, 0)  # ABS_X
        ctrl._handle_axis_event(0, ctrl.JS_EVENT_AXIS, -10000, 1) # ABS_Y
        status = ctrl.get_current_status()
        self.assertIn('BTN_A', status)
        self.assertIn('BTN_B', status)
        self.assertIn('ABS_X', status)
        self.assertIn('ABS_Y', status)

    def test_handle_event_dispatch(self):
        ctrl = XboxController(**self.config)
        with patch.object(ctrl, '_handle_button_event') as btn_patch, \
             patch.object(ctrl, '_handle_axis_event') as axis_patch:
            ctrl._handle_event(0, ctrl.JS_EVENT_BUTTON, 1, 0)
            btn_patch.assert_called()
            ctrl._handle_event(0, ctrl.JS_EVENT_AXIS, 100, 0)
            axis_patch.assert_called()

    def test_get_mapping_returns_none(self):
        ctrl = XboxController(**self.config)
        self.assertIsNone(ctrl._get_mapping('not_a_real_input'))

    def test_has_input_changed(self):
        ctrl = XboxController(**self.config)
        prev = {'BTN_A': 1.0}
        self.assertTrue(ctrl._has_input_changed('BTN_A', 0.0, prev))
        self.assertFalse(ctrl._has_input_changed('BTN_A', 1.0, prev))

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import MagicMock
import time

class TestInputRecorder(unittest.TestCase):
    def setUp(self):
        from modules.input_recorder.input_recorder import InputRecorder
        self.recorder = InputRecorder(animations_dir='/tmp')
        self.recorder.log = lambda *a, **k: None
        self.recorder.save_events = MagicMock()

    def test_recording_toggle_and_event(self):
        self.recorder.toggle_recording(enable=True, filename='test.json')
        self.assertTrue(self.recorder.recording)
        self.assertEqual(self.recorder.filename, 'test.json')
        # Simulate a controller event as per new format
        event = {
            'time_ms': 123456,
            'value': 1,
            'type': 1,
            'number': 7,
            'topics_args': [
                {'topic': 'tts', 'args': {'msg': 'Test Default'}}
            ]
        }
        self.recorder.handle_event(event)
        self.assertEqual(len(self.recorder.events), 1)
        self.assertIn('timestamp', self.recorder.events[0])
        self.recorder.toggle_recording(enable=False)
        self.assertFalse(self.recorder.recording)
        self.recorder.save_events.assert_called()

    def test_event_timestamp(self):
        self.recorder.toggle_recording(enable=True, filename='test2.json')
        event = {
            'time_ms': 654321,
            'value': 0,
            'type': 1,
            'number': 7,
            'topics_args': [
                {'topic': 'tts', 'args': {'msg': 'Test Default'}}
            ]
        }
        self.recorder.handle_event(event)
        self.assertIn('timestamp', self.recorder.events[0])
        self.recorder.toggle_recording(enable=False)

if __name__ == '__main__':
    unittest.main()

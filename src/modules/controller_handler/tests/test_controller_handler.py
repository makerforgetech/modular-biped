import unittest
from unittest.mock import MagicMock, patch
from modules.controller_handler.controller_handler import ControllerHandler

class TestControllerHandler(unittest.TestCase):

    def setUp(self):
        self.handler = ControllerHandler(
            mapping={'default': {}},
            modifier_buttons=[],
            debug=False
        )
        self.handler.messaging_service = MagicMock()

    def test_init(self):
        self.assertIsNone(self.handler.controller)
        self.assertFalse(self.handler.running)

    def test_start(self):
        self.handler.log = MagicMock()
        self.handler.start()
        self.assertTrue(self.handler.running)

    def test_loop_calls_process_input_when_running(self):
        self.handler.log = MagicMock()
        self.handler.running = True
        with patch.object(self.handler, '_process_input') as mock_pi:
            self.handler.loop()
            mock_pi.assert_called_once()

    def test_loop_does_not_call_process_input_when_not_running(self):
        self.handler.log = MagicMock()
        self.handler.running = False
        with patch.object(self.handler, '_process_input') as mock_pi:
            self.handler.loop()
            mock_pi.assert_not_called()

    def test_process_input_no_controller(self):
        self.handler.log = MagicMock()
        self.handler._process_input()
        self.handler.log.assert_called()

if __name__ == '__main__':
    unittest.main()

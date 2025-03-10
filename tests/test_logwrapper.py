import unittest
from unittest import mock
import os
import logging
from modules.logwrapper import LogWrapper

class TestLogWrapper(unittest.TestCase):

    @mock.patch('modules.logwrapper.logging')
    def test_init(self, mock_logging):
        log_wrapper = LogWrapper(path='/tmp', filename='test.log', log_level='info', cli_level='debug')
        self.assertEqual(log_wrapper.path, '/tmp')
        self.assertEqual(log_wrapper.filename, 'test.log')
        self.assertEqual(log_wrapper.file, '/tmp/test.log')
        self.assertEqual(log_wrapper.log_level, 'info')
        self.assertEqual(log_wrapper.cli_level, 'debug')
        mock_logging.basicConfig.assert_called_with(
            filename='/tmp/test.log',
            level=logging.INFO,
            format='%(levelname)s: %(asctime)s %(message)s',
            datefmt='%Y/%m/%d %I:%M:%S %p'
        )

    @mock.patch('modules.logwrapper.logging')
    def test_log(self, mock_logging):
        log_wrapper = LogWrapper(path='/tmp', filename='test.log', log_level='info', cli_level='debug')
        log_wrapper.log('Test message', type='info')
        mock_logging.log.assert_called_with(logging.INFO, 'Test message')

    @mock.patch('modules.logwrapper.logging')
    def test_log_json_message(self, mock_logging):
        log_wrapper = LogWrapper(path='/tmp', filename='test.log', log_level='info', cli_level='debug')
        log_wrapper.log('{"message": "Test JSON message"}', type='info')
        mock_logging.log.assert_called_with(logging.INFO, 'Test JSON message')

    @mock.patch('modules.logwrapper.logging')
    def test_log_with_translator(self, mock_logging):
        mock_translator = mock.Mock()
        mock_translator.request.return_value = 'Translated message'
        log_wrapper = LogWrapper(path='/tmp', filename='test.log', log_level='info', cli_level='debug', translator=mock_translator)
        log_wrapper.log('Test message', type='info')
        mock_translator.request.assert_called_with('Test message')
        mock_logging.log.assert_called_with(logging.INFO, 'Translated message')

    @mock.patch('modules.logwrapper.logging')
    def test_setup_messaging(self, mock_logging):
        log_wrapper = LogWrapper(path='/tmp', filename='test.log', log_level='info', cli_level='debug')
        with mock.patch.object(log_wrapper, 'subscribe') as mock_subscribe:
            log_wrapper.setup_messaging()
            mock_subscribe.assert_any_call('log', log_wrapper.log)
            mock_subscribe.assert_any_call('log/debug', log_wrapper.log, type='debug')
            mock_subscribe.assert_any_call('log/info', log_wrapper.log, type='info')
            mock_subscribe.assert_any_call('log/error', log_wrapper.log, type='error')
            mock_subscribe.assert_any_call('log/critical', log_wrapper.log, type='critical')
            mock_subscribe.assert_any_call('log/warning', log_wrapper.log, type='warning')

    @mock.patch('modules.logwrapper.os')
    def test_del(self, mock_os):
        log_wrapper = LogWrapper(path='/tmp', filename='test.log', log_level='info', cli_level='debug')
        log_wrapper.__del__()
        mock_os.path.isfile.assert_called_with('/tmp/test.log')
        mock_os.rename.assert_called_with('/tmp/test.log', '/tmp/test.log.previous')

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest import mock
from modules.pitemperature.pitemperature import PiTemperature

class TestPiTemperature(unittest.TestCase):

    @mock.patch('modules.pitemperature.pitemperature.os.popen')
    def test_monitor_critical_temp(self, mock_popen):
        mock_popen.return_value.readline.return_value = "temp=86'C"
        temp_module = PiTemperature()
        with mock.patch('modules.pitemperature.pitemperature.threading.Thread'):
            temp_module.messaging_service = mock.MagicMock()
        with mock.patch.object(temp_module, 'publish') as mock_publish, \
             mock.patch.object(temp_module, 'log') as mock_log:
            temp_module.monitor()
            # Should publish temperature and system/sleep
            mock_publish.assert_any_call('system/temperature', value='86')
            mock_publish.assert_any_call('system/sleep', requestor='PiTemperature')
            # Should log only the critical message
            mock_log.assert_called_with('Temperature is critical: 86°C', 'critical')


    @mock.patch('modules.pitemperature.pitemperature.os.popen')
    def test_monitor_high_temp(self, mock_popen):
        mock_popen.return_value.readline.return_value = "temp=81'C"
        temp_module = PiTemperature()
        with mock.patch('modules.pitemperature.pitemperature.threading.Thread'):
            temp_module.messaging_service = mock.MagicMock()
        with mock.patch.object(temp_module, 'publish') as mock_publish, \
             mock.patch.object(temp_module, 'log') as mock_log:
            temp_module.monitor()
            # Should publish temperature and system/throttle
            mock_publish.assert_any_call('system/temperature', value='81')
            mock_publish.assert_any_call('system/throttle', requestor='PiTemperature')
            # Should log only the warning message
            mock_log.assert_called_with('Temperature is high: 81°C', 'warning')


    @mock.patch('modules.pitemperature.pitemperature.os.popen')
    def test_monitor_normal_temp(self, mock_popen):
        mock_popen.return_value.readline.return_value = "temp=50'C"
        temp_module = PiTemperature()
        with mock.patch('modules.pitemperature.pitemperature.threading.Thread'):
            temp_module.messaging_service = mock.MagicMock()
        with mock.patch.object(temp_module, 'publish') as mock_publish, \
             mock.patch.object(temp_module, 'log') as mock_log:
            temp_module.monitor()
            # Should publish temperature and system/wake
            mock_publish.assert_any_call('system/temperature', value='50')
            mock_publish.assert_any_call('system/wake', requestor='PiTemperature')
            # Should log only the debug message
            mock_log.assert_called_with('Temperature: 50°C', 'debug')

    @mock.patch('modules.pitemperature.pitemperature.os.popen')
    @mock.patch('modules.pitemperature.pitemperature.sys.exit')
    def test_monitor_shutdown_temp(self, mock_exit, mock_popen):
        mock_popen.return_value.readline.return_value = "temp=91'C"
        temp_module = PiTemperature()
        with mock.patch('modules.pitemperature.pitemperature.threading.Thread'):
            temp_module.messaging_service = mock.MagicMock()
        with mock.patch.object(temp_module, 'publish') as mock_publish, \
             mock.patch.object(temp_module, 'log') as mock_log:
            temp_module.monitor()
            mock_publish.assert_any_call('system/temperature', value='91')
            # Should log only the critical message
            mock_log.assert_called_with('Temperature is too high exiting script: 91°C', 'critical')
            mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()
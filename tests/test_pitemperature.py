import unittest
from unittest import mock
from modules.pitemperature import PiTemperature

class TestPiTemperature(unittest.TestCase):

    @mock.patch('modules.pitemperature.os.popen')
    def test_monitor_critical_temp(self, mock_popen):
        mock_popen.return_value.readline.return_value = "temp=86'C"
        temp_module = PiTemperature()
        temp_module.messaging_service = mock.MagicMock()
        
        with mock.patch.object(temp_module, 'publish') as mock_publish, \
             mock.patch.object(temp_module, 'log') as mock_log:
            temp_module.monitor()
            mock_publish.assert_called_with('system/temperature', '86')
            mock_log.assert_called_with('Temperature is critical: 86°C', 'critical')

    @mock.patch('modules.pitemperature.os.popen')
    def test_monitor_high_temp(self, mock_popen):
        mock_popen.return_value.readline.return_value = "temp=81'C"
        temp_module = PiTemperature()
        temp_module.messaging_service = mock.MagicMock()
        
        with mock.patch.object(temp_module, 'publish') as mock_publish, \
             mock.patch.object(temp_module, 'log') as mock_log:
            temp_module.monitor()
            mock_publish.assert_called_with('system/temperature', '81')
            mock_log.assert_called_with('Temperature is high: 81°C', 'warning')

    @mock.patch('modules.pitemperature.os.popen')
    def test_monitor_normal_temp(self, mock_popen):
        mock_popen.return_value.readline.return_value = "temp=50'C"
        temp_module = PiTemperature()
        temp_module.messaging_service = mock.MagicMock()
        
        with mock.patch.object(temp_module, 'publish') as mock_publish, \
             mock.patch.object(temp_module, 'log') as mock_log:
            temp_module.monitor()
            mock_publish.assert_called_with('system/temperature', '50')
            mock_log.assert_called_with('Temperature: 50°C', 'debug')

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import MagicMock, patch
from modules.network.rtlsdr.rtlsdr import RTLSDR

class TestRTLSDR(unittest.TestCase):

    def test_init_defaults(self):
        sdr = RTLSDR()
        self.assertEqual(sdr.udp_host, '127.0.0.1')
        self.assertEqual(sdr.udp_port, 8433)
        self.assertIsNone(sdr.rtl_process)

    def test_setup_messaging(self):
        sdr = RTLSDR()
        with patch.object(sdr, 'subscribe') as mock_sub:
            sdr.setup_messaging()
            mock_sub.assert_any_call('sdr/start', sdr.start_rtl_433)
            mock_sub.assert_any_call('sdr/listen', sdr.listen_once)

if __name__ == '__main__':
    unittest.main()

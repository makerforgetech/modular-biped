from unittest import mock, TestCase
from modules.power import Power

@mock.patch('modules.power.pub', return_value=mock.Mock())
class PowerTest(TestCase):

    def test_init(self, mock_pub):
        mock_pub.sendMessage.reset_mock()
        power = Power(0)
        assert power.pin == 0
        assert power.active_count == 0
        mock_pub.sendMessage.assert_called()

    def test_use_release(self, mock_pub):
        mock_pub.sendMessage.reset_mock()
        power = Power(0)
        power.use()
        assert power.active_count == 1
        mock_pub.sendMessage.assert_has_calls([
            mock.call('serial', type=2, identifier=0, message=Power.STATE_OFF),
            mock.call('serial', type=2, identifier=0, message=Power.STATE_ON)])

        power.use()
        assert power.active_count == 2
        # No new calls
        assert mock_pub.sendMessage.call_count == 2

        power.use()
        assert power.active_count == 3
        # No new calls
        assert mock_pub.sendMessage.call_count == 2

        power.release()
        assert power.active_count == 2
        # No new calls
        assert mock_pub.sendMessage.call_count == 2

        power.release()
        assert power.active_count == 1
        # No new calls
        assert mock_pub.sendMessage.call_count == 2

        power.release()
        assert power.active_count == 0
        # New call
        assert mock_pub.sendMessage.call_count == 3
        # New call to disable
        mock_pub.sendMessage.assert_has_calls([
            mock.call('serial', type=2, identifier=0, message=Power.STATE_OFF),
            mock.call('serial', type=2, identifier=0, message=Power.STATE_ON),
            mock.call('serial', type=2, identifier=0, message=Power.STATE_OFF)])

        power.release()
        assert power.active_count == 0
        assert mock_pub.sendMessage.call_count == 3

        power.use()
        assert power.active_count == 1
        assert mock_pub.sendMessage.call_count == 4


    def test_use_exit(self, mock_pub):
        mock_pub.sendMessage.reset_mock()
        power = Power(0)
        power.use()
        assert power.active_count == 1
        mock_pub.sendMessage.assert_has_calls([
            mock.call('serial', type=2, identifier=0, message=Power.STATE_OFF),
            mock.call('serial', type=2, identifier=0, message=Power.STATE_ON)])

        power.exit()
        assert mock_pub.sendMessage.call_count == 3
        mock_pub.sendMessage.assert_has_calls([
            mock.call('serial', type=2, identifier=0, message=Power.STATE_OFF),
            mock.call('serial', type=2, identifier=0, message=Power.STATE_ON),
            mock.call('serial', type=2, identifier=0, message=Power.STATE_OFF)])

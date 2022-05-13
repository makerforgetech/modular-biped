from unittest.mock import Mock, call
from modules.mocks import mock_pubsub
from modules.mocks import mock_arduino_serial
from modules.power import Power
from modules.arduinoserial import ArduinoSerial


def test_init():
    mock_pubsub.module.pub.sendMessage.reset_mock()
    power = Power(0)
    assert power.pin == 0
    assert power.active_count == 0
    mock_pubsub.module.pub.sendMessage.assert_called()

def test_use_release():
    mock_pubsub.module.pub.sendMessage.reset_mock()
    power = Power(0)
    power.use()
    assert power.active_count == 1
    mock_pubsub.module.pub.sendMessage.assert_has_calls([
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_OFF),
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_ON)])

    power.use()
    assert power.active_count == 2
    # No new calls
    assert mock_pubsub.module.pub.sendMessage.call_count == 2

    power.use()
    assert power.active_count == 3
    # No new calls
    assert mock_pubsub.module.pub.sendMessage.call_count == 2

    power.release()
    assert power.active_count == 2
    # No new calls
    assert mock_pubsub.module.pub.sendMessage.call_count == 2

    power.release()
    assert power.active_count == 1
    # No new calls
    assert mock_pubsub.module.pub.sendMessage.call_count == 2

    power.release()
    assert power.active_count == 0
    # New call
    assert mock_pubsub.module.pub.sendMessage.call_count == 3
    # New call to disable
    mock_pubsub.module.pub.sendMessage.assert_has_calls([
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_OFF),
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_ON),
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_OFF)])

    power.release()
    assert power.active_count == 0
    assert mock_pubsub.module.pub.sendMessage.call_count == 3

    power.use()
    assert power.active_count == 1
    assert mock_pubsub.module.pub.sendMessage.call_count == 4


def test_use_exit():
    mock_pubsub.module.pub.sendMessage.reset_mock()
    power = Power(0)
    power.use()
    assert power.active_count == 1
    mock_pubsub.module.pub.sendMessage.assert_has_calls([
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_OFF),
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_ON)])

    power.exit()
    assert mock_pubsub.module.pub.sendMessage.call_count == 3
    mock_pubsub.module.pub.sendMessage.assert_has_calls([
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_OFF),
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_ON),
        call('serial', type=ArduinoSerial.DEVICE_PIN, identifier=0, message=Power.STATE_OFF)])

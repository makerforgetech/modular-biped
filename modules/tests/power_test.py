from modules.mocks.mock_pigpio import MockPiGPIO
import pigpio
from modules.power import Power


def test_init():
    power = Power(0)
    assert power.pin == 0
    assert power.active_count == 0
    assert power.pi is not None


def test_use_release():
    pi = pigpio.pi()
    # @todo mock threading
    power = Power(0, thread=False, pi=pi)  # don't use threading for tests
    power.use()
    assert power.active_count == 1
    assert pi.value == 1

    power.use()
    assert power.active_count == 2
    assert pi.value == 1

    power.use()
    assert power.active_count == 3
    assert pi.value == 1

    power.release()
    assert power.active_count == 2
    assert pi.value == 1

    power.release()
    assert power.active_count == 1
    assert pi.value == 1

    power.release()
    assert power.active_count == 0
    assert pi.value == 0

    power.release()
    assert power.active_count == 0
    assert pi.value == 0

    power.use()
    assert power.active_count == 1
    assert pi.value == 1

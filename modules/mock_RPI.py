import sys


# disable the real sleep command for faster unit tests
class MockGPIO:
    pulse = 0
    max_pulse = 0
    setmode_called = 0
    BCM = 1
    IN = 1
    PUD_UP = 1
    BOTH = 1

    # RPi.GPIO.setmode(RPi.GPIO.BCM)  # set up BCM GPIO numbering
    # RPi.GPIO.setup(self.pin, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
    # RPi.GPIO.add_event_detect(self.pin, RPi.GPIO.BOTH, callback=self.detect_motion)

    def setmode(mode):
        return mode

    def setup(pin, mode, **kwargs):
        return pin

    def input(pin):
        return pin

    def add_event_detect(pin, mode, **kwargs):
        return None


module = type(sys)('RPi')
module.GPIO = MockGPIO
sys.modules['RPi'] = module

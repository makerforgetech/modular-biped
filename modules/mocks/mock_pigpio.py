import sys

def pi():
    return MockPiGPIO()


class MockPiGPIO:
    pulse = 0
    max_pulse = 0
    setmode_called = 0
    value = None

    def set_mode(self, pin, mode):
        self.setmode_called = self.setmode_called + 1
        return self.setmode_called

    def set_servo_pulsewidth(self, pin, position):
        self.pulse = position
        if self.pulse > self.max_pulse:
            self.max_pulse = self.pulse
        return self.pulse

    # def get_servo_pulsewidth(self, pin):
    #     return self.pulse
    #
    def set_PWM_dutycycle(self, pin, val):
        self.pulse = val
        if self.pulse > self.max_pulse:
            self.max_pulse = self.pulse
        return self.pulse

    def write(self, pin, value):
        self.value = value
        return value

module = type(sys)('pigpio')
module.pi = pi
module.OUTPUT = True
sys.modules['pigpio'] = module
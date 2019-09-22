from modules.actuators.stepper import StepperMotor


class LinearActuator:
    def __init__(self, pin1, pin2, pin3, pin4, pwm_range, start, **kwargs):
        self.stepper = StepperMotor(pin1, pin2, pin3, pin4)
        self.range = pwm_range
        self.start = start
        self.pos = start
        self.increment = 1  # step increment
        self.power = kwargs.get('power', None)

    def move(self, percentage):
        if 0 <= percentage <= 100:
            if self.power:
                self.power.use()
            new = self.translate(percentage)

            while new != pos:
                if new > pos:
                    # move up
                    self.stepper.doСlockwiseStep()
                    pos = pos + self.increment
                elif new < pos:
                    # move down
                    self.stepper.doСounterclockwiseStep()
                    pos = pos - self.increment
            if self.power:
                self.power.release()

        else:
            raise ValueError('Percentage %d out of range' % percentage)

    def reset(self):
        self.move(self.start)

    def translate(self, value):
        # Figure out how 'wide' each range is
        leftSpan = 100 - 0
        rightSpan = self.range[1] - self.range[0]

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return self.range[0] + (valueScaled * rightSpan)

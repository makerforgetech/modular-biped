from modules.actuators.stepper import StepperMotor


class LinearActuator:
    def __init__(self, pins, pwm_range, start, **kwargs):
        self.stepper = StepperMotor(pins)
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
                    self.stepper.c_step()
                    pos = pos + self.increment
                elif new < pos:
                    # move down
                    self.stepper.cc_step()
                    pos = pos - self.increment
            if self.power:
                self.power.release()

        else:
            raise ValueError('Percentage %d out of range' % percentage)

    def reset(self):
        self.move(self.start)

    def translate(self, value):
        # Figure out how 'wide' each range is
        left_span = 100 - 0
        right_span = self.range[1] - self.range[0]

        # Convert the left range into a 0-1 range (float)
        value_scaled = float(value) / float(left_span)

        # Convert the 0-1 range into a value in the right range.
        return self.range[0] + (value_scaled * right_span)

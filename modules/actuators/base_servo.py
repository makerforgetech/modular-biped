import threading
from time import sleep
from modules.base_module import BaseModule

class BaseServo(BaseModule):

    def __init__(self, **kwargs):
        """
        BaseServo class
        Handles generic functionality for all servo types
        
        :param kwargs: pin, name, id, range, power, start_pos, buffer, delta
        :param pin: GPIO pin number
        :param name: servo name
        :param id: servo id
        :param range: [min, max] angle range
        :param power: True to use power
        :param start_pos: initial angle
        :param buffer: PWM amount to specify as acceleration / deceleration buffer
        :param delta: amount of change in acceleration / deceleration (as a multiple)
        """
        self.pin = kwargs.get('pin')
        self.identifier = kwargs.get('name')
        self.index = kwargs.get('id')
        self.range = kwargs.get('range')
        self.power = kwargs.get('power', False)

        self.start = kwargs.get('start_pos', 50)
        self.pos = self.translate(self.start)
        self.buffer = kwargs.get('buffer', 0)  # PWM amount to specify as acceleration / deceleration buffer
        self.delta = kwargs.get('delta', 1.5)  # amount of change in acceleration / deceleration (as a multiple)

        self.move(self.start)

    def setup_messaging(self):
        self.subscribe('servo:' + self.identifier + ':mvabs', self.move)
        self.subscribe('servo:' + self.identifier + ':mv', self.move_relative)

    def move_relative(self, percentage, safe=True):
        new = self.pos + (self.translate(percentage) - self.range[0])
        if new > self.range[1] and safe:
            new = self.range[1]
        elif new < self.range[0] and safe:
            new = self.range[0]
        if self.range[0] <= new <= self.range[1]:
            this_move = self.calculate_move(self.pos, new)
            self.execute_move(this_move, True)
            self.pos = new
        else:
            self.publish('log/error', '[Servo] Percentage %d out of range' % percentage)
            raise ValueError('Percentage %d out of range' % percentage)

    def move(self, percentage, safe=True):
        if 0 <= percentage <= 100 or safe:
            new = self.translate(percentage)
            if new > self.range[1] and safe:
                new = self.range[1]
            elif new < self.range[0] and safe:
                new = self.range[0]
            self.execute_move([(percentage, 0)])
            self.pos = new
        else:
            self.publish('log/error', '[Servo] Percentage %d out of range' % percentage)
            raise ValueError('Percentage %d out of range' % percentage)

    def execute_move(self, sequence, is_relative=False):
        """
        Recursive function to handle each movement in sequence.
        Move to first position then set thread.Timer for next movement after delay specified in movement 1.
        Repeat until there are no more movements in sequence
        :param sequence:
        :return:
        """
        print('Moving servo...')
        s = sequence.pop(0)

        if self.power:
            self.publish('power:use')
        self.perform_move(s[0])
        if len(sequence) > 1:
            timer = threading.Timer(s[1], self.execute_move, [sequence])
            timer.start()
        if self.power and self.pos == self.start:
            self.publish('power:release')

    def perform_move(self, position):
        raise NotImplementedError("Subclasses should implement this!")

    def calculate_move(self, old, new, time=0.1, translate=False):
        if translate:
            old = self.translate(old)
            new = self.translate(new)
        current = old if self.buffer > 0 else new

        increment = 1
        decelerate = False

        safety = 1000  # quit after 1000 iterations, in case something has gone wrong

        sequence = []

        while safety:
            safety = safety - 1
            sequence.append((current, time if self.buffer > 0 else 0.5))

            if current == new:
                return sequence

            if old < new:
                if increment < self.buffer and not decelerate:
                    increment = increment * self.delta if increment * self.delta < self.buffer else self.buffer
                    current = current + increment if current + increment < new else new
                elif decelerate:
                    increment = increment / self.delta if increment / self.delta > 1 else 1
                    current = current + increment if current + increment < new else new
                else:
                    current = new - self.buffer
                    decelerate = True
            else:
                if increment < self.buffer and not decelerate:
                    increment = increment * self.delta if increment * self.delta < self.buffer else self.buffer
                    current = current - increment if current - increment > new else new
                elif decelerate:
                    increment = increment / self.delta if increment / self.delta > 1 else 1
                    current = current - increment if current - increment > new else new
                else:
                    current = new + self.buffer
                    decelerate = True

    def reset(self):
        self.move(self.start)
    
    def translate(self, value):
        leftSpan = 100 - 0
        rightSpan = self.range[1] - self.range[0]
        valueScaled = float(value) / float(leftSpan)
        return self.range[0] + (valueScaled * rightSpan)
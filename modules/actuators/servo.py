import pigpio
import threading
from modules.config import Config
from modules.arduinoserial import ArduinoSerial
from time import sleep
from pubsub import pub

class Servo:

    def __init__(self, pin, identifier, pwm_range, **kwargs):
        self.pin = pin
        self.identifier = identifier
        self.range = pwm_range
        self.power = kwargs.get('power', True)

        self.start = kwargs.get('start_pos', 50)
        self.pos = self.translate(self.start)
        self.buffer = kwargs.get('buffer', 0)  # PWM amount to specify as acceleration / deceleration buffer
        self.delta = kwargs.get('delta', 1.5)  # amount of change in acceleration / deceleration (as a multiple)

        # Accepts either serial connection or PI pin
        self.serial = kwargs.get('serial', True)
        if self.serial is None:
            self.pi = kwargs.get('pi', pigpio.pi())
            self.pi.set_mode(pin, pigpio.OUTPUT)

        self.move(self.start)

        pub.subscribe(self.move, 'servo:' + identifier + ':mvabs')
        pub.subscribe(self.move_relative, 'servo:' + identifier + ':mv')

    def __del__(self):
        pass #self.reset()

    def move_relative(self, percentage, safe=True):
        new = self.pos + (self.translate(percentage) - self.range[0])
        if new > self.range[1] and safe:
            new = self.range[1]
        elif new < self.range[0] and safe:
            new = self.range[0]
        if self.range[0] <= new <= self.range[1]:
            this_move = self.calculate_move(self.pos, new)
            self.execute_move(this_move)
            self.pos = new
        else:
            pub.sendMessage('log:error', '[Servo] Percentage %d out of range' % percentage)
            raise ValueError('Percentage %d out of range' % percentage)

    def move(self, percentage, safe=True):
        if 0 <= percentage <= 100 or safe:
            new = self.translate(percentage)
            if new > self.range[1] and safe:
                new = self.range[1]
            elif new < self.range[0] and safe:
                new = self.range[0]
            self.execute_move(self.calculate_move(self.pos, new))
            self.pos = new
        else:
            pub.sendMessage('log:error', '[Servo] Percentage %d out of range' % percentage)
            raise ValueError('Percentage %d out of range' % percentage)

    def execute_move(self, sequence):
        """
        Recursive function to handle each movement in sequence.
        Move to first position then set thread.Timer for next movement after delay specified in movement 1.
        Repeat until there are no more movements in sequence
        :param sequence:
        :return:
        """
        s = sequence.pop(0)

        # @todo this prevents initial set of position
        # # ignore request if position matches current position
        # if s[0] == self.pos:
        #     return

        if self.power:
            pub.sendMessage('power:use')
        if self.serial:
            # print(int(s[0]))
            pub.sendMessage('serial', type=ArduinoSerial.DEVICE_SERVO, identifier=self.pin, message=s[0])
        else:
            self.pi.set_servo_pulsewidth(self.pin, s[0])
        if len(sequence) > 1:
            timer = threading.Timer(s[1], self.execute_move, [sequence])
            timer.start()
        else:
            pass #sleep(s[1])
        if self.power and self.pos == self.start:
            pub.sendMessage('power:release')

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

            # Accelerate / Decelerate
            # @todo simplify
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
        # Figure out how 'wide' each range is
        leftSpan = 100 - 0
        rightSpan = self.range[1] - self.range[0]

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return self.range[0] + (valueScaled * rightSpan)

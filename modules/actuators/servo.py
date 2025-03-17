import pigpio
import threading
from modules.config import Config
from modules.network.arduinoserial import ArduinoSerial
from time import sleep
from modules.base_module import BaseModule

class Servo(BaseModule):

    def __init__(self, **kwargs):
        """
        Servo class
        Uses ArduinoSerial to communicate with Arduino
        
        :param kwargs: pin, name, id, range, power, start_pos, buffer, delta, serial, pi
        :param pin: GPIO pin number
        :param name: servo name
        :param id: servo id
        :param range: [min, max] angle range
        :param power: True to use power
        :param start_pos: initial angle
        :param buffer: PWM amount to specify as acceleration / deceleration buffer
        :param delta: amount of change in acceleration / deceleration (as a multiple)
        :param serial: True to use serial connection
        
        Install: pip install pigpio (optional, untested in this version)
        
        Subscribes to 'servo:<name>:mvabs' to move servo to absolute position
        - Argument: percentage (int) - percentage to move servo
        
        Subscribes to 'servo:<name>:mv' to move servo to relative position
        - Argument: percentage (int) - percentage to move servo
        
        Example:
        self.publish('servo:pan:mvabs', percentage=90)
        self.publish('servo:pan:mv', percentage=10)
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

        # Accepts either serial connection or PI pin
        self.serial = kwargs.get('serial', True)
        if self.serial is None:
            self.pi = kwargs.get('pi', pigpio.pi())
            self.pi.set_mode(self.pin, pigpio.OUTPUT)

    def setup_messaging(self):
        self.subscribe('servo:' + self.identifier + ':mvabs', self.move)
        self.subscribe('servo:' + self.identifier + ':mv', self.move_relative)
        
        self.move(self.start) # @todo move to a more appropriate place, can't be in init because messaging is not set up yet

    def __del__(self):
        pass #self.reset()

    def move_relative(self, percentage, safe=True):
        # Only calculate relative position if not using serial
        # Otherwise it is done by the arduino
        if not self.serial:
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
        else:
            self.execute_move([(percentage, 0)], True)

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

        # @todo this prevents initial set of position
        # # ignore request if position matches current position
        # if s[0] == self.pos:
        #     return

        if self.power:
            self.publish('power:use')
        if self.serial:
            # just move the pan servo for now. Remove after debugging
            # if self.index != 7 and self.index != 6 and self.index != 5 and self.index != 4  and self.index != 3  and self.index != 2:
                # return
            type = ArduinoSerial.DEVICE_SERVO
            if is_relative:
                type = ArduinoSerial.DEVICE_SERVO_RELATIVE
            self.publish('serial', type=type, identifier=self.index, message=s[0])
        else:
            self.pi.set_servo_pulsewidth(self.pin, s[0])
        if len(sequence) > 1:
            timer = threading.Timer(s[1], self.execute_move, [sequence])
            timer.start()
        else:
            pass #sleep(s[1])
        if self.power and self.pos == self.start:
            self.publish('power:release')

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

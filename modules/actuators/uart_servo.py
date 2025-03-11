import pigpio
from modules.network.arduinoserial import ArduinoSerial
from modules.actuators.base_servo.py import BaseServo

class UARTServo(BaseServo):

    def __init__(self, **kwargs):
        """
        UARTServo class
        Uses ArduinoSerial to communicate with Arduino
        
        :param kwargs: pin, name, id, range, power, start_pos, buffer, delta, serial, pi
        """
        super().__init__(**kwargs)
        self.serial = kwargs.get('serial', True)
        if self.serial is None:
            self.pi = kwargs.get('pi', pigpio.pi())
            self.pi.set_mode(self.pin, pigpio.OUTPUT)

    def perform_move(self, position):
        if self.serial:
            type = ArduinoSerial.DEVICE_SERVO
            self.publish('serial', type=type, identifier=self.index, message=position)
        else:
            self.pi.set_servo_pulsewidth(self.pin, position)
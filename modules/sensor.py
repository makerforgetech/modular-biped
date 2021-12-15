import pigpio
from pubsub import pub

class Sensor:
    def __init__(self, pin, **kwargs):
        self.pi = kwargs.get('pi', pigpio.pi())
        self.pin = pin
        self.value = None
        pub.subscribe(self.loop, 'loop:1')

    def loop(self):
        if self.read():
            pub.sendMessage('motion')

    def read(self):
        self.value = self.pi.read(self.pin)
        return self.value

    def watch(self, edge, callback):
        """
        :param edge: pigpio.EITHER_EDGE, pigpio.FALLING_EDGE, pigpio.RISING_EDGE
        :param callback: method to call when change detected
        """
        return self.pi.callback(self.pin, edge, callback)

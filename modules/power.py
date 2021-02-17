import threading
from pubsub import pub
from modules.arduinoserial import ArduinoSerial

class Power:
    def __init__(self, pin, **kwargs):
        self.pin = pin
        self.active_count = 0
        self.thread = kwargs.get('thread', True)
        self.timer = None
        pub.subscribe(self.use, 'power:use')
        pub.subscribe(self.release, 'power:release')
        pub.sendMessage('serial', type=ArduinoSerial.DEVICE_PIN, identifier=self.pin, message=1)  # high is off, low is on

    def __del__(self):
        if self.timer is not None:
            self.timer.cancel()

    def use(self):
        self.active_count = self.active_count + 1
        pub.sendMessage('serial', type=ArduinoSerial.DEVICE_PIN, identifier=self.pin, message=0)
        if self.timer is not None:
            self.timer.cancel()

    def release(self):
        self.active_count = self.active_count - 1
        if self.active_count <= 0:
            self.active_count = 0  # just ensure that it hasn't gone below 0
            if self.thread:
                if self.timer is not None:
                    self.timer.cancel()
                self.timer = threading.Timer(10.0, self._off)
                self.timer.start()
            else:
                self._off()

    def _off(self):
        if self.active_count <= 0:
            print('off')
            pub.sendMessage('serial', type=ArduinoSerial.DEVICE_PIN, identifier=self.pin, message=1)
import pigpio
import threading


class Power:
    def __init__(self, pin, **kwargs):
        self.pin = pin
        self.active_count = 0
        self.pi = kwargs.get('pi', pigpio.pi())
        self.thread = kwargs.get('thread', True)
        self.pi.set_mode(pin, pigpio.OUTPUT)
        self.timer = None

    def use(self):
        print('on')
        self.active_count = self.active_count + 1
        self.pi.write(self.pin, 1)
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
            self.pi.write(self.pin, 0)


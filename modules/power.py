import pigpio
import threading


class Power:
    def __init__(self, pin):
        self.pin = pin
        self.active_count = 0
        self.pi = pigpio.pi()
        self.pi.set_mode(pin, pigpio.OUTPUT)

    def use(self):
        print('on')
        self.active_count = self.active_count + 1
        self.pi.write(self.pin, 1)

    def release(self):
        self.active_count = self.active_count - 1
        if self.active_count <= 0:
            timer = threading.Timer(10.0, self._off)  # @todo mock threading
            timer.start()

    def _off(self):
        if self.active_count <= 0:
            print('off')
            self.pi.write(self.pin, 0)

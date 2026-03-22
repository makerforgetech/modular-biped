import threading
from pubsub import pub


class Power:
    STATE_ON = 0
    STATE_OFF = 1

    def __init__(self, pin, **kwargs):
        self.pin = pin
        self.active_count = 0
        self.thread = kwargs.get('thread', True)
        self.timer = None
        self.device_type = kwargs.get('device_type', 2)
        pub.subscribe(self.use, 'power:use')
        pub.subscribe(self.release, 'power:release')
        pub.subscribe(self.exit, 'power:exit')
        pub.sendMessage('serial', type=self.device_type, identifier=self.pin, message=Power.STATE_OFF)  # high is off, low is on

    def __del__(self):
        if self.timer is not None:
            self.timer.cancel()

    def exit(self):
        pub.sendMessage('serial', type=self.device_type, identifier=self.pin, message=Power.STATE_OFF)

    def use(self):
        self.active_count = self.active_count + 1
        if self.active_count == 1:
            pub.sendMessage('serial', type=self.device_type, identifier=self.pin, message=Power.STATE_ON)
        if self.timer is not None:
            self.timer.cancel()

    def release(self):
        if self.active_count == 0:
            return
        self.active_count = self.active_count - 1
        if self.active_count <= 0:
            self.active_count = 0  # just ensure that it hasn't gone below 0
            pub.sendMessage('serial', type=self.device_type, identifier=self.pin, message=Power.STATE_OFF)
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
            pub.sendMessage('serial', type=self.device_type, identifier=self.pin, message=Power.STATE_OFF)

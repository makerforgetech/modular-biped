from evdev import InputDevice, categorize, ecodes
from select import select
from pubsub import pub
from threading import Thread

class Gamepad:
    KEY_UP = 103
    KEY_DOWN = 108
    KEY_LEFT = 105
    KEY_RIGHT = 106
    LEFT_CLICK = 272
    RIGHT_CLICK = 273
    SPACE = 57
    BACKSPACE = 14
    RETURN = 28
    KEY_T = 20
    KEY_Y = 21
    # KEY_Q = 4

    def __init__(self, **kwargs):
        self.running = False
        # A mapping of file descriptors (integers) to InputDevice instances.
        self.devices = map(InputDevice, ('/dev/input/event0', '/dev/input/event1'))
        self.devices = {dev.fd: dev for dev in self.devices}
        self.start()

    def __del__(self):
        self.running = False
        pub.sendMessage('log', msg='[Gamepad] Stopping')

    def start(self):
        self.running = True
        pub.sendMessage('log', msg='[Gamepad] Starting')
        Thread(target=self.handle_input, args=()).start()
        return self

    def handle_input(self):
        while True:
            if not self.running:
                break
            r, w, x = select(self.devices, [], [])
            for fd in r:
                for event in self.devices[fd].read():
                    pub.sendMessage('puppet')
                    if event.type == ecodes.EV_KEY and event.value == 1:
                        if event.code == Gamepad.KEY_UP:
                            pub.sendMessage('servo:tilt:mv', percentage=-5)
                            print('up')
                        elif event.code == Gamepad.KEY_LEFT:
                            pub.sendMessage('servo:pan:mv', percentage=5)
                            print('left')
                        elif event.code == Gamepad.KEY_RIGHT:
                            pub.sendMessage('servo:pan:mv', percentage=-5)
                            print('right')
                        elif event.code == Gamepad.KEY_DOWN:
                            pub.sendMessage('servo:tilt:mv', percentage=5)
                            print('down')
                        elif event.code == Gamepad.LEFT_CLICK:
                            pub.sendMessage('speak', message='hi')
                        elif event.code == Gamepad.RIGHT_CLICK:
                            pub.sendMessage('boredom:action')
                        elif event.code == Gamepad.SPACE:
                            pub.sendMessage('animate', action='stand')
                        elif event.code == Gamepad.BACKSPACE:
                            pub.sendMessage('animate', action='sit')
                        elif event.code == Gamepad.RETURN:
                            pub.sendMessage('animate', action='wake')
                        elif event.code == Gamepad.KEY_T:
                            pub.sendMessage('vision:timelapse:start')
                        elif event.code == Gamepad.KEY_Y:
                            pub.sendMessage('vision:timelapse:stop')
                        # elif event.code == Gamepad.KEY_Q:
                        #     raise pub.sendMessage('exit')
                        else:
                            print(event)
                    else:
                        print(event)



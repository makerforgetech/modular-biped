from pubsub import pub
from time import sleep
from colour import Color

try:
    import board
    import neopixel
except:
    pass

import threading

class LED:
    COLOR_OFF = (0, 0, 0)
    COLOR_RED = (5, 0, 0)
    COLOR_GREEN = (0, 5, 0)
    COLOR_BLUE = (0, 0, 5)
    COLOR_PURPLE = (5, 0, 5)
    COLOR_WHITE = (5, 5, 5)
    COLOR_WHITE_FULL = (255, 255, 255)
    COLOR_RED_TO_GREEN_100 = list(Color("red").range_to(Color("green"),100))

    COLOR_MAP = {
        'red': COLOR_RED,
        'green': COLOR_GREEN,
        'blue': COLOR_BLUE,
        'purple': COLOR_PURPLE,
        'white': COLOR_WHITE,
        'white_full': COLOR_WHITE_FULL,
        'off': COLOR_OFF
    }

    def __init__(self, count, **kwargs):
        # Initialise
        self.count = count
        self.positions = {
            'right' : 0,
            'top_right': 1,
            'top_left' : 2,
            'left' : 3,
            'bottom_left' : 4,
            'bottom_right' : 5,
            'middle': 6,
            'top1': 7,
            'top2': 8,
            'top3': 9,
            'top4': 10,
            'top5': 11
        }
        self.all = range(self.count)
        self.all_eye = range(6)
        self.animation = False
        self.thread = None
        self.overridden = False  # prevent any further changes until released (for flashlight)
        try:
            self.pixels = neopixel.NeoPixel(board.D12, count)
        except:
            pass
        # Default states
        self.set(self.all, LED.COLOR_OFF)
        sleep(0.1)
        self.set(self.positions['middle'], LED.COLOR_BLUE)

        # Set subscribers
        pub.subscribe(self.set, 'led')
        pub.subscribe(self.full, 'led:full')
        pub.subscribe(self.eye, 'led:eye')
        pub.subscribe(self.off, 'led:off')
        pub.subscribe(self.eye, 'led:flashlight')
        pub.subscribe(self.party, 'led:party')
        pub.subscribe(self.exit, 'exit')
        pub.subscribe(self.speech, 'speech')

    def exit(self):
        """
        On close of application carry out clean up
        """
        if self.animation:
            self.animation = False
            self.thread.join()
        self.set(self.all, LED.COLOR_OFF)
        sleep(1)

    def speech(self, msg):
        if 'light on' in msg:
            self.flashlight(True)
        if 'light off' in msg:
            self.flashlight(False)

    def set(self, identifiers, color):
        """
        Set color of pixel
        (255, 0, 0) # set to red, full brightness
        (0, 128, 0) # set to green, half brightness
        (0, 0, 64)  # set to blue, quarter brightness
        :param identifiers: pixel number (starting from 0) - can be list
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        """
        if self.overridden:
            return
        # convert single identifier to list
        if type(identifiers) is int:
            identifiers = [identifiers]
        elif type(identifiers) is str:
            identifiers = [self.positions[identifiers]]
        # lookup color if string
        if type(color) is float:
            color = int(color)
        if type(color) is int:
            # Make color gradiant use possible @todo refactor
            if color >= 100:
                color = 99 # max in range
            color = LED.COLOR_RED_TO_GREEN_100[color].rgb
            color = (color[0]*10, color[1]*10, color[2]*10) # increase values to be used as LED RGB
        elif type(color) is str:
            color = LED.COLOR_MAP[color]
        for i in identifiers:
            if type(i) is str:
                i = self.positions[i]
            #print(str(i) + str(color))
            try:
                self.pixels[i] = color
            except Exception as e:
                print(e)
                pub.sendMessage('log', msg='[LED] Error in set pixels')
                pass
        sleep(0.1)

    def flashlight(self, on):
        if on:
            self.set(self.all, LED.COLOR_WHITE_FULL)
            self.overridden = True
        else:
            self.overridden = False
            self.set(self.all, LED.COLOR_OFF)

    def off(self):
        if self.thread:
            pub.sendMessage('log', msg='[LED] Animation stopping')
            self.animation = False
            self.thread.animation = False
            self.thread.join()
        self.set(self.all, LED.COLOR_OFF)
        sleep(.5)

    def full(self, color):
        if color in LED.COLOR_MAP.keys():
            self.set(self.all, LED.COLOR_MAP[color])

    def eye(self, color):
        if color in LED.COLOR_MAP.keys() and self.pixels[self.positions['middle']] != color:
            pub.sendMessage('log', msg='[LED] Setting eye colour: ' + color)
            self.set(self.positions['middle'], LED.COLOR_MAP[color])

    def party(self, color):
        # self.animate(self.all, 'off', 'rainbow_cycle')

        for j in range(256 * 1):
            for i in range(self.count):
                self.set(i, LED._wheel((int(i * 256 / self.count) + j) & 255))
            return
        print('done')

        # threading.Thread(target=self.rainbow_cycle(self.all, 'off'))
        # self.thread.start()

    def animate(self, identifiers, color, animation):
        """
        Trigger one of the LED animations
        :param identifiers: single index or array or indexes
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        :param animation: string name of animation listed in map below
        :return:
        """
        if self.animation:
            pub.sendMessage('log', msg='[LED] Animation already started. Command ignored')
            return

        pub.sendMessage('log', msg='[LED] Animation starting: ' + animation)

        animations = {
            'spinner': self.spinner,
            'breathe': self.breathe,
            'rainbow': self.rainbow,
            'rainbow_cycle': self.rainbow_cycle
        }

        self.animation = True
        if animation in animations:
            self.thread = threading.Thread(target=animations[animation], args=(identifiers, color,))
        self.thread.start()


    def spinner(self, identifiers, color, index=1):
        """
        Create a spinner effect around outer LEDs of 7 LED ring.
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        :param index: current LED to change
        :return:
        """
        sleep(.3)

        self.set(range(1, 7), LED.COLOR_OFF)
        self.set(index, color)

        index = (index + 1) % self.count
        # don't set the center led
        if index == 0:
            index = 1

        t = threading.currentThread()
        if getattr(t, "animation", True):
            self.spinner(identifiers, color, index)

    def breathe(self, identifiers, color):
        """
        Begin a breathing animation for whatever color has been passed in.

        Assume the max is the brightest value from the tuple.
        All values > 0 will become aligned to that max value.
        E.g. (0, 100, 255) will brighten to (0, 255, 255) and then darken to (0, 0, 0) repeatedly

        :param identifiers: pins to apply animation
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        """
        if type(color) is str:
            color = LED.COLOR_MAP[color]
        t = threading.currentThread()
        if getattr(t, "animation", True):
            for dc in range(0, max(color), 1):  # Increase brightness to max of color
                self.set(identifiers, (dc if color[0] > 0 else 0, dc if color[0] > 0 else 0, dc if color[0] > 0 else 0))
                sleep(0.10)
            sleep(2)
            for dc in range(max(color), 0, -1):  # Decrease brightness to 0
                self.set(identifiers, (dc if color[0] > 0 else 0, dc if color[0] > 0 else 0, dc if color[0] > 0 else 0))
                sleep(0.10)
            sleep(2)

    @staticmethod
    def _wheel(p):
        """Generate rainbow colors across 0-255 positions."""
        # https://github.com/jgarff/rpi_ws281x/blob/master/python/examples/strandtest.py
        if p < 85:
            return (p * 3, 255 - p * 3, 0)
        elif p < 170:
            p -= 85
            return (255 - p * 3, 0, p * 3)
        else:
            p -= 170
            return (0, p * 3, 255 - p * 3)

    def rainbow(self, identifiers, color, wait_ms=20, iterations=1):
        """Draw rainbow that fades across all pixels at once."""
        for j in range(256 * iterations):
            for i in range(self.count):
                self.set(i, LED._wheel((i + j) & 255))
            t = threading.currentThread()
            if not getattr(t, "animation", True):
                return
            sleep(wait_ms / 1000)

    def rainbow_cycle(self, identifiers, color, wait_ms=20, iterations=5):
        """Draw rainbow that uniformly distributes itself across all pixels."""
        for j in range(256 * iterations):
            for i in range(self.count):
                self.set(i, LED._wheel((int(i * 256 / self.count) + j) & 255))
            t = threading.currentThread()
            if not getattr(t, "animation", True):
                return
            sleep(wait_ms / 1000)

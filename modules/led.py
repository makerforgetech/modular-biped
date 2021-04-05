from pubsub import pub
from time import sleep

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
    COLOR_WHITE = (255, 255, 255)

    COLOR_MAP = {
        'red': COLOR_RED,
        'green': COLOR_GREEN,
        'blue': COLOR_BLUE,
        'white': COLOR_WHITE,
        'off': COLOR_OFF
    }

    def __init__(self, count, **kwargs):
        # Initialise
        self.count = count
        self.middle = kwargs.get('middle', 6)
        self.all = range(self.count)
        self.animation = False
        self.thread = None
        try:
            self.pixels = neopixel.NeoPixel(board.D12, count)
        except:
            pass
        # Default states
        self.set(self.all, LED.COLOR_OFF)
        sleep(0.1)
        self.set(self.middle, LED.COLOR_BLUE)

        # Set subscribers
        pub.subscribe(self.set, 'led')
        pub.subscribe(self.full, 'led:full')
        pub.subscribe(self.eye, 'led:eye')
        pub.subscribe(self.off, 'led:off')
        pub.subscribe(self.eye, 'led:flashlight')
        pub.subscribe(self.animate, 'led:animate')
        pub.subscribe(self.exit, 'exit')

    def exit(self):
        """
        On close of application carry out clean up
        """
        if self.animation:
            self.animation = False
            self.thread.join()
        self.set(self.all, LED.COLOR_OFF)
        sleep(1)

    def set(self, identifiers, color):
        """
        Set color of pixel
        (255, 0, 0) # set to red, full brightness
        (0, 128, 0) # set to green, half brightness
        (0, 0, 64)  # set to blue, quarter brightness
        :param identifiers: pixel number (starting from 0) - can be list
        :param color: string map of COLOR_MAP or tuple (R, G, B)
        """
        # convert single identifier to list
        if type(identifiers) is int:
            identifiers = [identifiers]
        # lookup color if string
        if type(color) is str:
            color = LED.COLOR_MAP[color]
        for i in identifiers:
            #print(str(i) + str(color))
            try:
                self.pixels[i] = color
            except:
                pass
        sleep(0.1)

    def flashlight(self, on):
        if on:
            self.set(self.all, LED.COLOR_WHITE)
        else:
            self.set(self.all, LED.COLOR_OFF)
            sleep(0.1)
            self.eye('green')

    def off(self):
        if self.thread:
            print('ANIMATION STOPPING')
            self.animation = False
            self.thread.animation = False
            self.thread.join()
        self.set(self.all, LED.COLOR_OFF)
        sleep(2)

    def full(self, color):
        if color in LED.COLOR_MAP.keys():
            self.set(self.all, LED.COLOR_MAP[color])

    def eye(self, color):
        if color in LED.COLOR_MAP.keys() and self.pixels[self.middle] != color:
            self.set(self.middle, LED.COLOR_MAP[color])

    def animate(self, identifiers, color, animation):
        if self.animation:
            print('ANIMATION ALREADY STARTED')
            return

        print('ANIMATION STARTING: ' + animation)

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
                sleep(0.05)
            sleep(1)
            for dc in range(max(color), 0, -1):  # Decrease brightness to 0
                self.set(identifiers, (dc if color[0] > 0 else 0, dc if color[0] > 0 else 0, dc if color[0] > 0 else 0))
                sleep(0.05)
            sleep(1)

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

from pubsub import pub
from modules.arduinoserial import ArduinoSerial
from time import sleep
import board
import neopixel


class LED:
    COLOUR_OFF = (0, 0, 0)
    COLOUR_RED = (5, 0, 0)
    COLOUR_GREEN = (0, 5, 0)
    COLOUR_BLUE = (0, 0, 5)
    COLOUR_WHITE = (255, 255, 255)

    COLOUR_MAP = {
        'red': COLOUR_RED,
        'green': COLOUR_GREEN,
        'blue': COLOUR_BLUE,
        'white': COLOUR_WHITE,
        'off': COLOUR_OFF
    }

    def __init__(self, count, **kwargs):
        self.count = count
        self.middle = kwargs.get('middle', 0)
        self.all = range(self.count)
        pub.subscribe(self.set, 'led')
        pub.subscribe(self.eye, 'led:eye')
        pub.subscribe(self.eye, 'led:flashlight')
        self.pixels = neopixel.NeoPixel(board.D12, count)
        self.set(self.all, LED.COLOUR_OFF)
        sleep(0.1)
        self.set(self.middle, LED.COLOUR_GREEN)
        self.leds = []
        for x in range(0, count):
            self.leds.insert(x, LED.COLOUR_OFF)

    def exit(self):
        self.set(self.all, LED.COLOUR_OFF)
        sleep(1)

    def set(self, identifiers, color):
        """
        Set color of pixel
        (255, 0, 0) # set to red, full brightness
        (0, 128, 0) # set to green, half brightness
        (0, 0, 64)  # set to blue, quarter brightness
        :param identifiers: pixel number (starting from 0) - can be list
        :param color: (R, G, B)
        """
        if type(identifiers) is int:
            identifiers = [identifiers]
        for i in identifiers:
            self.pixels[identifiers[i]] = color

    def flashlight(self, on):
        if on:
            self.set(self.all, LED.COLOUR_WHITE)
        else:
            self.set(self.all, LED.COLOUR_OFF)
            sleep(0.1)
            self.eye('green')

    def eye(self, color):
        if color in LED.COLOUR_MAP.keys() and self.leds[self.middle] != color:
            # print(LED.COLOUR_MAP[color])
            self.leds[self.middle] = color
            self.set(self.middle, LED.COLOUR_MAP[color])

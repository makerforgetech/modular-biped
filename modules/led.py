from pubsub import pub
from modules.config import Config
from modules.arduinoserial import ArduinoSerial
from time import sleep

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

    def __init__(self, count):
        self.count = count
        pub.subscribe(self.set, 'led')
        self.set(Config.LED_ALL, LED.COLOUR_OFF)
        sleep(0.1)
        self.set(Config.LED_MIDDLE, LED.COLOUR_GREEN)

    def exit(self):
        self.set(Config.LED_ALL, LED.COLOUR_OFF)
        sleep(1)

    def set(self, identifiers, color):
        """
        Set color of pixel
        (255, 0, 0) # set to red, full brightness
        (0, 128, 0) # set to green, half brightness
        (0, 0, 64)  # set to blue, quarter brightness
        :param number: pixel number (starting from 0) - can be list
        :param color: (R, G, B)
        """
        pub.sendMessage('serial', type=ArduinoSerial.DEVICE_LED, identifier=identifiers, message=color)

    def flashlight(self, on):
        if on:
            self.set(Config.LED_ALL, LED.COLOUR_WHITE)
        else:
            self.set(Config.LED_ALL, LED.COLOUR_OFF)
            sleep(0.1)
            self.eye('green')

    def eye(self, color):
        if color in LED.COLOUR_MAP.keys():
            print(LED.COLOUR_MAP[color])
            self.set(Config.LED_MIDDLE, LED.COLOUR_MAP[color])

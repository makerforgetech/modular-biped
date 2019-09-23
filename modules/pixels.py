# sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel

import neopixel

class NeoPixel:
    def __init__(self, pin, count):
        self.pin = pin
        self.count = count
        self.pixels = neopixel.NeoPixel(self.pin, self.count)

    def __del__(self):
        i = 0
        while i < self.count:
            self.pixels[i] = (0, 0, 0)

    def set(self, number, color):
        self.pixels[number] = color  # (255, 0, 0)

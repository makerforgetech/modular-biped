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
        """
        Set color of pixel
        (255, 0, 0) # set to red, full brightness
        (0, 128, 0) # set to green, half brightness
        (0, 0, 64)  # set to blue, quarter brightness
        :param number: pixel number (starting from 0)
        :param color: (R, G, B)
        """
        self.pixels[number] = color

    def fill(self, color):
        self.pixels.fill(color)

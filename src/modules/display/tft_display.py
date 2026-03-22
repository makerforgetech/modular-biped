#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import spidev as SPI
from PIL import Image
from modules.base_module import BaseModule
from modules.display.lib import LCD_1inch28

class TFTDisplay(BaseModule):
    def __init__(self, **kwargs):
        self.rotation = kwargs.get('rotation', 0)
        try:
            spi = SPI.SpiDev(kwargs.get('bus'), kwargs.get('device'))
            spi.max_speed_hz = 10000000
            self.disp = LCD_1inch28.LCD_1inch28(
                spi=spi, spi_freq=10000000, rst=kwargs.get('rst_pin'),
                dc=kwargs.get('dc_pin'), bl=kwargs.get('bl_pin')
            )
            self.img = None
            self.clear_display()
            self.background = None
            self.set_background('BLACK')
            self.disp.ShowImage(self.background)
            
            if kwargs.get('test_on_boot'):
                self.draw_image('makerforge_bl.png')
        except Exception as e:
            logging.error(f"Failed to initialize TFT display: {e}")
            
    def exit(self):
        self.log("Exiting TFT display module, clearing display")
        self.set_background('BLACK')
        self.show_image(self.background)
        self.disp.bl_DutyCycle(0)
        self.disp = None # Prevents further use

    def setup_messaging(self):
        self.subscribe('display/background', self.set_background)
        self.subscribe('system/exit', self.exit)

    def set_background(self, color=None):
        if color is not None:
            self.background = Image.new("RGBA", (self.disp.width, self.disp.height), color)

    def clear_display(self):
        disp = self.disp
        disp.Init()
        disp.clear()
        disp.bl_DutyCycle(50)
        return disp

    def draw_image(self, img):
        disp = self.disp
        image = Image.open(os.getcwd() + '/src/modules/display/images/' + img)
        new_image = image.resize((disp.width, disp.height)).rotate(self.rotation)
        self.show_image(new_image)

    def blink(self, off_time=0.2):
        disp = self.disp
        image = self.img
        if (image is None) or (not isinstance(image, Image.Image)):
            raise ValueError("Image must be a valid PIL Image object.")
        self.show_image(self.background)
        time.sleep(off_time)
        self.show_image(image)
    
    def show_image(self, image):
        if self.disp is None:
            return
        self.disp.ShowImage(image)

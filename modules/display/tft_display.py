#!/usr/bin/python
# -*- coding: UTF-8 -*-
#import chardet
import os
import sys 
import time
import logging
import spidev as SPI
sys.path.append("..")
from modules.display.lib import LCD_1inch28
from PIL import Image,ImageDraw,ImageFont

class TFTDisplay:
    def __init__(self, **kwargs):
        try:
            # Open SPI bus
            spi = SPI.SpiDev(kwargs.get('bus'), kwargs.get('device'))
            spi.max_speed_hz = 10000000

            # Display with hardware SPI:
            ''' Warning!!! Don't create multiple display objects!!! '''
            self.disp = LCD_1inch28.LCD_1inch28(spi=spi, spi_freq=10000000, rst=kwargs.get('rst_pin'), dc=kwargs.get('dc_pin') , bl=kwargs.get('bl_pin'))
            if kwargs.get('test_on_boot'):
                self.test_display()
           
        except Exception as e:
            logging.error(f"Failed to initialize TFT display: {e}")
            
    def test_display(self):
        disp = self.disp
        # Initialize library.
        disp.Init()
        # Clear display.
        disp.clear()
        # Set the backlight to 100
        disp.bl_DutyCycle(50)
        print("TFT display initialized")
        # Create blank image for drawing.
        image1 = Image.new("RGB", (disp.width, disp.height), "BLACK")
        draw = ImageDraw.Draw(image1)
        
        draw.arc((1, 1, 239, 239), 0, 360, fill=(0, 0, 255))
        draw.arc((2, 2, 238, 238), 0, 360, fill=(0, 0, 255))
        draw.arc((3, 3, 237, 237), 0, 360, fill=(0, 0, 255))
        
        draw.line([(120, 1), (120, 12)], fill=(128, 255, 128), width=4)
        draw.line([(120, 227), (120, 239)], fill=(128, 255, 128), width=4)
        draw.line([(1, 120), (12, 120)], fill=(128, 255, 128), width=4)
        draw.line([(227, 120), (239, 120)], fill=(128, 255, 128), width=4)
        
        # Display the image
        disp.ShowImage(image1)
        print("TFT display test completed")
         
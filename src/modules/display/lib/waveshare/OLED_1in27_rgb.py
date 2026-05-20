# /*****************************************************************************
# * | File        :	  OLED_1in27_rgb.py
# * | Author      :   Waveshare team
# * | Function    :   Driver for OLED_1in5_rgb
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2023-04-15
# * | Info        :   
# ******************************************************************************/
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from . import config
import time
import numpy as np

Device_SPI = config.Device_SPI
Device_I2C = config.Device_I2C

OLED_WIDTH   = 128  # OLED width
OLED_HEIGHT  = 96   # OLED height

class OLED_1in27_rgb(config.RaspberryPi):
        
    """    Write register address and data     """
    def command(self, cmd):
        self.digital_write(self.DC_PIN,False)
        self.spi_writebyte([cmd])

    """    Write data     """
    def data(self, data):
        self.digital_write(self.DC_PIN,True)
        self.spi_writebyte([data])

    def Init(self):
        if (self.module_init() != 0):
            return -1

        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT
        """Initialize dispaly"""    
        self.reset()

        if(self.Device == Device_I2C):
            print ("Only Device_SPI, Please revise config.py !!!")
            exit()  
            
        self.command(0xfd) # command lock
        self.data(0x12)
        self.command(0xfd)  # command lock
        self.data(0xB1)

        self.command(0xae)  # display off
        self.command(0xa4)  # Normal Display mode

        self.command(0x15)  # set column address
        self.data(0x00)     # column address start 00
        self.data(0x7f)     # column address end 127
        self.command(0x75)  # set row address
        self.data(0x00)     # row address start 00
        self.data(0x5f)     # row address end 95   

        self.command(0xB3)
        self.data(0xF1)

        self.command(0xCA)
        self.data(0x7F)

        self.command(0xa0)  # set re-map & data format
        self.data(0x74)     # Horizontal address increment

        self.command(0xa1)  # set display start line
        self.data(0x60)     # start 96 line

        self.command(0xa2)  # set display offset
        self.data(0x00)

        self.command(0xAB)
        self.command(0x01)

        self.command(0xB4)
        self.data(0xA0)
        self.data(0xB5)
        self.data(0x55)

        self.command(0xC1)
        self.data(0xC8)
        self.data(0x80)
        self.data(0xC0)

        self.command(0xC7)
        self.data(0x0F)

        self.command(0xB1)
        self.data(0x32)

        self.command(0xB2)
        self.data(0xA4)
        self.data(0x00)
        self.data(0x00)

        self.command(0xBB)
        self.data(0x17)

        self.command(0xB6)
        self.data(0x01)

        self.command(0xBE)
        self.data(0x05)

        self.command(0xA6)

        time.sleep(0.1)
        self.command(0xAF)  # turn on oled panel
        
   
    def reset(self):
        """Reset the display"""
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,False)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)

    def clear(self):
        _buffer = [0x00]*(self.width * self.height * 2)
        self.ShowImage(_buffer)             
    
    def getbuffer(self, image):
        buf = [0x00] * ((self.width*2) * self.height)
        imwidth, imheight = image.size
        pixels = image.load()
        for y in range(imheight):
            for x in range(imwidth):
                # Set the bits for the column of pixels at the current position.
                buf[x*2 + y*imwidth*2] = ((pixels[x,y][0] & 0xF8) | (pixels[x,y][1] >> 5))
                buf[x*2+1 + y*imwidth*2] = (((pixels[x,y][1]<<3) & 0xE0) | (pixels[x,y][2] >> 3))
        return buf   

    def ShowImage(self, pBuf):
        self.command(0x15) # set column address
        self.data(0x00)    # column address start 00
        self.data(0x7f)    # column address end 127
        self.command(0x75) # set row address
        self.data(0x00)    # row address start 00
        self.data(0x5f)    # row address end 95   
        self.command(0x5C); 
        for i in range(0, self.height):
            for j in range(0, self.width*2):
                self.data(pBuf[j + self.width*2*i])
        return

       
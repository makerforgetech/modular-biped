# /*****************************************************************************
# * | File        :	  OLED_1in51.py
# * | Author      :   Waveshare team
# * | Function    :   Driver for OLED_1in51
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2022-07-14
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

OLED_WIDTH   = 128 #OLED width
OLED_HEIGHT  = 64  #OLED height

class OLED_1in51(config.RaspberryPi):

    """    Write register address and data     """
    def command(self, cmd):
        if(self.Device == Device_SPI):
            self.digital_write(self.DC_PIN,False)
            self.spi_writebyte([cmd])
        else:
            self.i2c_writebyte(0x00, cmd)

    def Init(self):
        if (self.module_init() != 0):
            return -1

        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT

        """Initialize dispaly"""    
        self.reset()
        self.command(0xAE);#--turn off oled panel

        self.command(0x00);#---set low column address
        self.command(0x10);#---set high column address

        self.command(0x20)
        self.command(0x00)
            
        self.command(0xFF)
        
        self.command(0xA6)
        
        self.command(0xA8) 
        self.command(0x3F)
        
        self.command(0xD3)
        self.command(0x00)
        
        self.command(0xD5)
        self.command(0x80)
        
        self.command(0xD9)
        self.command(0x22)

        self.command(0xDA)
        self.command(0x12)
        
        self.command(0xDB)
        self.command(0x40)
        time.sleep(0.1)
        self.command(0xAF);#--turn on oled panel
        
   
    def reset(self):
        """Reset the display"""
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,False)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)
    
    def getbuffer(self, image):
        buf = [0xFF] * ((self.width//8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        if(imwidth == self.width and imheight == self.height):
            # print ("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[x + (y // 8) * self.width] &= ~(1 << (y % 8))        
        elif(imwidth == self.height and imheight == self.width):
            # print ("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[(newx + (newy // 8 )*self.width) ] &= ~(1 << (y % 8))
        return buf
            
    def ShowImage(self, pBuf):
        for page in range(0,8):
            # set page address #
            self.command(0xB0 + page)
            # set low column address #
            self.command(0x00); 
            # set high column address #
            self.command(0x10); 
            # write data #
            time.sleep(0.01)
            if(self.Device == Device_SPI):
                self.digital_write(self.DC_PIN,True)
            for i in range(0,self.width):
                if(self.Device == Device_SPI):
                    self.spi_writebyte([~pBuf[i+self.width*page]]); 
                else :
                    self.i2c_writebyte(0x40, ~pBuf[i+self.width*page])
                       
    def clear(self):
        """Clear contents of image buffer"""
        _buffer = [0xff]*(self.width * self.height//8)
        self.ShowImage(_buffer) 

       
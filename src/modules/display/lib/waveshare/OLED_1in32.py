# /*****************************************************************************
# * | File        :	  OLED_1in32.py
# * | Author      :   Waveshare team
# * | Function    :   Driver for OLED_1in32
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2023-02-13
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

OLED_WIDTH   = 128  #OLED width
OLED_HEIGHT  = 96   #OLED height

class OLED_1in32(config.RaspberryPi):

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

        self.command(0xae)  # turn off oled panel

        self.command(0xa0)  # set re-map       
        self.command(0x51)          

        self.command(0xa1)  # set display start line 
        self.command(0x00)

        self.command(0xa2)  # set display offset 
        self.command(0x20)    

        self.command(0xa4)  # normal display

        self.command(0xa8)  # set multiplex ratio 
        self.command(0x5f)

        self.command(0xab)  # function selection A 
        self.command(0x01)  # enable internal VDD regulator

        self.command(0x81)  # set contrast
        self.command(0x77)    

        self.command(0xb1)  # set phase length 
        self.command(0x31)  

        self.command(0xb3)  # set front clock divider/oscillator frequency
        self.command(0xb1)

        self.command(0xb4)  # For brightness enhancement
        self.command(0xb5)          

        self.command(0xb6)  # Set Second pre-charge Period
        self.command(0X0d)      

        self.command(0xbc)  # Set Pre-charge voltage
        self.command(0x07)      

        self.command(0xbe)  # set vcomh
        self.command(0x07)       

        self.command(0xd5)  # Function Selection B
        self.command(0x02)  # Enable second pre-charge         

        time.sleep(0.1)
        self.clear()
        self.command(0xAF)  # turn on oled panel

        
    def reset(self):
        """Reset the display"""
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,False)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)

    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        if((Xstart > self.width) or (Ystart > self.height) or
        (Xend > self.width) or (Yend > self.height)):
            return
        self.command(0x15)
        self.command(Xstart//2)
        self.command(Xend//2 - 1)

        self.command(0x75)
        self.command(Ystart)
        self.command(Yend - 1)


    def clear(self):
        _buffer = [0x00]*(self.width * self.height//2)
        self.ShowImage(_buffer)             

    
    def getbuffer(self, image):
        buf = [0xff] * ((self.width//2) * self.height)
        image_monocolor = image.convert('L')#convert
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        if(imwidth == self.width and imheight == self.height):
            print ("horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    addr = (int)(x/2 + y*64)
                    color = pixels[x, y] % 16
                    data = buf[addr] & (~0xf0 >> (x%2)*4)
                    buf[addr] &= data | ((color<<4) >> ((x%2)*4))
        elif(imwidth == self.height and imheight == self.width):
            print ("Vertical")
            for y in range(imheight):       # 128
                for x in range(imwidth):    # 96
                    # Set the bits for the column of pixels at the current position.
                    addr = (int)(y/2 + (95-x)*64)
                    color = pixels[x, y] % 16
                    data = buf[addr] & (~0xf0 >> (y%2)*4)
                    buf[addr] &= data | ((color<<4) >> ((y%2)*4))
        return buf   
        

    def ShowImage(self, pBuf):
        self.SetWindows(0, 0, 128, 96)
        if(self.Device == Device_SPI):
            self.digital_write(self.DC_PIN,True)
        for i in range(0, self.height):
            for j in range(0, self.width//2):
                if(self.Device == Device_SPI):
                    self.spi_writebyte([pBuf[j+self.width//2*i]])
                else:
                    self.i2c_writebyte(0x40, pBuf[j+self.width//2*i])
        return


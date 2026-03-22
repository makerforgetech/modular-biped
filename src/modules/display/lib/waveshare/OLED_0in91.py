# /*****************************************************************************
# * | File        :	  OLED_0in91.py
# * | Author      :   Waveshare team
# * | Function    :   Driver for OLED_0in91
# * | Info        :
# *----------------
# * | This version:   V2.0
# * | Date        :   2020-08-18
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
OLED_HEIGHT  = 32  #OLED height

class OLED_0in91(config.RaspberryPi):
        
    """    Write register address and data     """
    def command(self, cmd):
        self.i2c_writebyte(0x00, cmd)

    def data(self, data):
        self.i2c_writebyte(0x40, data)

    def Init(self):  
        if (self.module_init() != 0):
            return -1

        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT
        self.Column = OLED_WIDTH
        self.Page = int(OLED_HEIGHT//8)

        if(self.Device == Device_SPI):
            print ("Only Device_I2C, Please revise config.py !!!")
            exit()    
            
        self.reset()
        """Initialize dispaly"""      
        #print("initialize register bgin")
        self.command(0xAE)

        self.command(0x40) # set low column address
        self.command(0xB0) # set high column address

        self.command(0xC8) # not offset

        self.command(0x81)
        self.command(0xff)

        self.command(0xa1)

        self.command(0xa6)

        self.command(0xa8)
        self.command(0x1f)

        self.command(0xd3)
        self.command(0x00)

        self.command(0xd5)
        self.command(0xf0)

        self.command(0xd9)
        self.command(0x22)

        self.command(0xda)
        self.command(0x02)

        self.command(0xdb)
        self.command(0x49)

        self.command(0x8d)
        self.command(0x14) 
        time.sleep(0.2)
        self.command(0xaf) #turn on OLED display 
        #print("initialize register over")
        
    def reset(self):
        """Reset the display"""
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,False)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)
    
    def getbuffer(self, image):
        buf = [0xff] * (self.Page * self.Column)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        if(imwidth == self.width and imheight == self.height):
            # print ("Horizontal screen")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[x + int(y / 8) * self.width] &= ~(1 << (y % 8))
        elif(imwidth == self.height and imheight == self.width):
            # print ("Vertical screen")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[(newx + int(newy / 8 )*self.width) ] &= ~(1 << (y % 8))
        for x in range(self.Page * self.Column):
            buf[x] = ~buf[x]
        return buf 
            
    def ShowImage(self, pBuf):
        for i in range(0, self.Page):            
            self.command(0xB0 + i) # set page address
            self.command(0x00) # set low column address
            self.command(0x10) # set high column address
            # write data #
            for j in range(0, self.Column):
                self.data(pBuf[j+self.width*i])
                    
    def clear(self):
        """Clear contents of image buffer"""
        _buffer = [0x00]*(self.width * self.height//8)
        self.ShowImage(_buffer)        
       
# /*****************************************************************************
# * | File        :	  OLED_1in3.py
# * | Author      :   Waveshare team
# * | Function    :   Driver for OLED_1in3_c
# * | Info        :
# *----------------
# * | This version:   V2.0
# * | Date        :   2020-08-14
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

class OLED_1in3(config.RaspberryPi):

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
        time.sleep(0.1)
        self.command(0xAE)#--turn off oled panel
        self.command(0x02)#---set low column address
        self.command(0x10)#---set high column address
        self.command(0x40)#--set start line address  Set Mapping RAM Display Start Line (0x00~0x3F)
        self.command(0x81)#--set contrast control register
        self.command(0xA0)#--Set SEG/Column Mapping     
        self.command(0xC0)#Set COM/Row Scan Direction   
        self.command(0xA6)#--set normal display
        self.command(0xA8)#--set multiplex ratio(1 to 64)
        self.command(0x3F)#--1/64 duty
        self.command(0xD3)#-set display offset    Shift Mapping RAM Counter (0x00~0x3F)
        self.command(0x00)#-not offset
        self.command(0xd5)#--set display clock divide ratio/oscillator frequency
        self.command(0x80)#--set divide ratio, Set Clock as 100 Frames/Sec
        self.command(0xD9)#--set pre-charge period
        self.command(0xF1)#Set Pre-Charge as 15 Clocks & Discharge as 1 Clock
        self.command(0xDA)#--set com pins hardware configuration
        self.command(0x12)
        self.command(0xDB)#--set vcomh
        self.command(0x40)#Set VCOM Deselect Level
        self.command(0x20)#-Set Page Addressing Mode (0x00/0x01/0x02)
        self.command(0x02)#
        self.command(0xA4)# Disable Entire Display On (0xa4/0xa5)
        self.command(0xA6)# Disable Inverse Display On (0xa6/a7) 
        time.sleep(0.1)
        self.command(0xAF)#--turn on oled panel
        
   
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
            print ("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[x + (y // 8) * self.width] &= ~(1 << (y % 8))        
        elif(imwidth == self.height and imheight == self.width):
            print ("Vertical")
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
            self.command(0x02) 
            # set high column address #
            self.command(0x10) 
            # write data #
            # time.sleep(0.01)
            if(self.Device == Device_SPI):
                self.digital_write(self.DC_PIN,True)
            for i in range(0,self.width):
                if(self.Device == Device_SPI):
                    # self.digital_write(self._dc,True)
                    self.spi_writebyte([~pBuf[i+self.width*page]]) 
                else :
                    self.i2c_writebyte(0x40, ~pBuf[i+self.width*page])
                       
    def clear(self):
        """Clear contents of image buffer"""
        _buffer = [0xff]*(self.width * self.height//8)
        self.ShowImage(_buffer) 

       
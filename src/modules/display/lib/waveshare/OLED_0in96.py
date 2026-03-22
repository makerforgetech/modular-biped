# /*****************************************************************************
# * | File        :	  OLED_0in96.py
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

SSD1306_SETCONTRAST  = 0x81
SSD1306_DISPLAYALLON_RESUME  = 0xA4
SSD1306_DISPLAYALLON  = 0xA5
SSD1306_NORMALDISPLAY  = 0xA6
SSD1306_INVERTDISPLAY  = 0xA7
SSD1306_DISPLAYOFF  = 0xAE
SSD1306_DISPLAYON  = 0xAF
SSD1306_SETDISPLAYOFFSET  = 0xD3
SSD1306_SETCOMPINS  = 0xDA
SSD1306_SETVCOMDETECT  = 0xDB
SSD1306_SETDISPLAYCLOCKDIV  = 0xD5
SSD1306_SETPRECHARGE  = 0xD9
SSD1306_SETMULTIPLEX  = 0xA8
SSD1306_SETLOWCOLUMN  = 0x00
SSD1306_SETHIGHCOLUMN  = 0x10
SSD1306_SETSTARTLINE  = 0x40
SSD1306_MEMORYMODE  = 0x20
SSD1306_COLUMNADDR  = 0x21
SSD1306_PAGEADDR  = 0x22
SSD1306_COMSCANINC  = 0xC0
SSD1306_COMSCANDEC  = 0xC8
SSD1306_SEGREMAP  = 0xA0
SSD1306_CHARGEPUMP  = 0x8D
SSD1306_EXTERNALVCC  = 0x01
SSD1306_SWITCHCAPVCC  = 0x02

#Scrolling constants
SSD1306_ACTIVATE_SCROLL  = 0x2F
SSD1306_DEACTIVATE_SCROLL  = 0x2E
SSD1306_SET_VERTICAL_SCROLL_AREA  = 0xA3
SSD1306_RIGHT_HORIZONTAL_SCROLL  = 0x26
SSD1306_LEFT_HORIZONTAL_SCROLL  = 0x27
SSD1306_VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL  = 0x29
SSD1306_VERTICAL_AND_LEFT_HORIZONTAL_SCROLL  = 0x2A

Device_SPI = config.Device_SPI
Device_I2C = config.Device_I2C

OLED_WIDTH   = 128 #OLED width
OLED_HEIGHT  = 64  #OLED height

class OLED_0in96(config.RaspberryPi):

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

        self.reset()
        """Initialize dispaly"""      
        self.command(SSD1306_DISPLAYOFF) 
        self.command(SSD1306_SETDISPLAYCLOCKDIV) 
        self.command(0x80)                               # the suggested ratio 0x80

        self.command(SSD1306_SETMULTIPLEX) 
        self.command(0x3F) 
        self.command(SSD1306_SETDISPLAYOFFSET) 
        self.command(0x0)                                # no offset
        self.command(SSD1306_SETSTARTLINE | 0x0)         # line #0
        self.command(SSD1306_CHARGEPUMP)
        self.command(0x14) 

        self.command(SSD1306_MEMORYMODE) 
        self.command(0x00)                               # 0x0 act like ks0108

        self.command(SSD1306_SEGREMAP | 0x1) 
        self.command(SSD1306_COMSCANDEC) 
        self.command(SSD1306_SETCOMPINS) 
        self.command(0x12)            # TODO - calculate based on _rawHieght ?
        self.command(SSD1306_SETCONTRAST) 
        self.command(0xCF) 
        self.command(SSD1306_SETPRECHARGE) 
        self.command(0xF1) 
        self.command(SSD1306_SETVCOMDETECT) 
        self.command(0x40) 
        self.command(SSD1306_DISPLAYALLON_RESUME) 
        self.command(SSD1306_NORMALDISPLAY) 
        self.command(SSD1306_DISPLAYON) 
        
    def reset(self):
        """Reset the display"""
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,False)
        time.sleep(0.1)
        self.digital_write(self.RST_PIN,True)
        time.sleep(0.1)
    
    def SetWindows(self, Xstart, Xend, Ystart, Yend):
        self.command(SSD1306_COLUMNADDR) 
        self.command(Xstart)            #cloumn start address
        self.command(Xend-1)              #cloumn end address
        self.command(SSD1306_PAGEADDR) 
        self.command(Ystart)          #page atart address
        self.command(Yend-1)            #page end address

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
    
    
    def ShowImage(self,Image):
        self.SetWindows(0, self.width, 0, self.height//8)
        for i in range(0,self.width * self.height//8):
            if(self.Device == Device_SPI):
                self.digital_write(self.DC_PIN,True)
                self.spi_writebyte([~Image[i]])
            # else:
            #     config.i2c_writebyte(0x40, ~Image[i])

    

    def clear(self):
        """Clear contents of image buffer"""
        _buffer = [0xff]*(self.width * self.height//8)
        self.ShowImage(_buffer)          
       
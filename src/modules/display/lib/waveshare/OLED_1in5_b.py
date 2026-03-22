# /*****************************************************************************
# * | File        :	  OLED_1in5_b.py
# * | Author      :   Waveshare team
# * | Function    :   Driver for OLED_1in5_b
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2023-05-20
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
OLED_HEIGHT  = 128  #OLED height

class OLED_1in5_b(config.RaspberryPi):

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
        self.command(0xae)    
        self.command(0x00)  
        self.command(0x10)   

        self.command(0xB0)    
        
        self.command(0xdc)    
        self.command(0x20)  

        self.command(0x81) 
        self.command(0x6f)    
        
        self.command(0x21)  
        
        self.command(0xa1)   
        
        self.command(0xc0)
        self.command(0xa4)   

        self.command(0xa6)   
        
        self.command(0xa8)  
        self.command(0x7f)    
      
        self.command(0xd3)   
        self.command(0x60)

        self.command(0xd5)  
        self.command(0x80)
            
        self.command(0xd9)   
        self.command(0x1d)  

        self.command(0xdb)  
        self.command(0x35) 

        self.command(0xad)  
        self.command(0x80)  
        time.sleep(0.2)
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
        image_monocolor = image.convert('1')#convert
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        # if(imwidth == self.width and imheight == self.height):
        for y in range(imheight):
            for x in range(imwidth):
                # Set the bits for the column of pixels at the current position.
                if pixels[x, y] == 0:
                    buf[y*16 + x//8] &= ~(1 <<  (x % 8))                    
        return buf 


    
    def ShowImage(self, pBuf):
        self.command(0xB0)
        for page in range(0,self.height):
            # set low column address #
            self.command(0x00 + (page & 0x0f))
            # set high column address #
            self.command(0x10 + (page >> 4))
            # write data #
            # time.sleep(0.01)
            if(self.Device == Device_SPI):
                self.digital_write(self.DC_PIN,True)
            for i in range(0,self.width//8):
                if(self.Device == Device_SPI):
                    self.spi_writebyte([pBuf[i+self.width//8*page]])
                else :
                    self.i2c_writebyte(0x40, pBuf[i+self.width//8*page])
                       
    def clear(self):
        """Clear contents of image buffer"""
        _buffer = [0x00]*(self.width * self.height//8)
        self.ShowImage(_buffer) 

       
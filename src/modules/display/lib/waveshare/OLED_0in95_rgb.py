# /*****************************************************************************
# * | File        :	  OLED_1in5_rgb.py
# * | Author      :   Waveshare team
# * | Function    :   Driver for OLED_1in5_rgb
# * | Info        :
# *----------------
# * | This version:   V2.0
# * | Date        :   2020-08-17
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

DRAW_LINE                       = 0x21
DRAW_RECTANGLE                  = 0x22
COPY_WINDOW                     = 0x23
DIM_WINDOW                      = 0x24
CLEAR_WINDOW                    = 0x25
FILL_WINDOW                     = 0x26
DISABLE_FILL                    = 0x00
ENABLE_FILL                     = 0x01
CONTINUOUS_SCROLLING_SETUP      = 0x27
DEACTIVE_SCROLLING              = 0x2E
ACTIVE_SCROLLING                = 0x2F

SET_COLUMN_ADDRESS              = 0x15
SET_ROW_ADDRESS                 = 0x75
SET_CONTRAST_A                  = 0x81
SET_CONTRAST_B                  = 0x82
SET_CONTRAST_C                  = 0x83
MASTER_CURRENT_CONTROL          = 0x87
SET_PRECHARGE_SPEED_A           = 0x8A
SET_PRECHARGE_SPEED_B           = 0x8B
SET_PRECHARGE_SPEED_C           = 0x8C
SET_REMAP                       = 0xA0
SET_DISPLAY_START_LINE          = 0xA1
SET_DISPLAY_OFFSET              = 0xA2
NORMAL_DISPLAY                  = 0xA4
ENTIRE_DISPLAY_ON               = 0xA5
ENTIRE_DISPLAY_OFF              = 0xA6
INVERSE_DISPLAY                 = 0xA7
SET_MULTIPLEX_RATIO             = 0xA8
DIM_MODE_SETTING                = 0xAB
SET_MASTER_CONFIGURE            = 0xAD
DIM_MODE_DISPLAY_ON             = 0xAC
DISPLAY_OFF                     = 0xAE
NORMAL_BRIGHTNESS_DISPLAY_ON    = 0xAF
POWER_SAVE_MODE                 = 0xB0
PHASE_PERIOD_ADJUSTMENT         = 0xB1
DISPLAY_CLOCK_DIV               = 0xB3
SET_GRAy_SCALE_TABLE            = 0xB8
ENABLE_LINEAR_GRAY_SCALE_TABLE  = 0xB9
SET_PRECHARGE_VOLTAGE           = 0xBB

SET_V_VOLTAGE                   = 0xBE

Device_SPI = config.Device_SPI
Device_I2C = config.Device_I2C

OLED_WIDTH   = 96  #OLED width
OLED_HEIGHT  = 64  #OLED height

class OLED_0in95_rgb(config.RaspberryPi):

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
            
        self.command(DISPLAY_OFF)          #Display Off
        self.command(SET_CONTRAST_A)       #Set contrast for color A
        self.command(0xFF)                     #145 0x91
        self.command(SET_CONTRAST_B)       #Set contrast for color B
        self.command(0xFF)                     #80 0x50
        self.command(SET_CONTRAST_C)       #Set contrast for color C
        self.command(0xFF)                     #125 0x7D
        self.command(MASTER_CURRENT_CONTROL)#master current control
        self.command(0x06)                     #6
        self.command(SET_PRECHARGE_SPEED_A)#Set Second Pre-change Speed For ColorA
        self.command(0x64)                     #100
        self.command(SET_PRECHARGE_SPEED_B)#Set Second Pre-change Speed For ColorB
        self.command(0x78)                     #120
        self.command(SET_PRECHARGE_SPEED_C)#Set Second Pre-change Speed For ColorC
        self.command(0x64)                     #100
        self.command(SET_REMAP)            #set remap & data format
        self.command(0x72)                     #0x72              
        self.command(SET_DISPLAY_START_LINE)#Set display Start Line
        self.command(0x0)
        self.command(SET_DISPLAY_OFFSET)   #Set display offset
        self.command(0x0)
        self.command(NORMAL_DISPLAY)       #Set display mode
        self.command(SET_MULTIPLEX_RATIO)  #Set multiplex ratio
        self.command(0x3F)
        self.command(SET_MASTER_CONFIGURE) #Set master configuration
        self.command(0x8E)
        self.command(POWER_SAVE_MODE)      #Set Power Save Mode
        self.command(0x00)                     #0x00
        self.command(PHASE_PERIOD_ADJUSTMENT)#phase 1 and 2 period adjustment
        self.command(0x31)                     #0x31
        self.command(DISPLAY_CLOCK_DIV)    #display clock divider/oscillator frequency
        self.command(0xF0)
        self.command(SET_PRECHARGE_VOLTAGE)#Set Pre-Change Level
        self.command(0x3A)
        self.command(SET_V_VOLTAGE)        #Set vcomH
        self.command(0x3E)
        self.command(DEACTIVE_SCROLLING)   #disable scrolling

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

    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.command(SET_COLUMN_ADDRESS)
        self.command(Xstart)         #cloumn start address
        self.command(Xend - 1)         #cloumn end address
        self.command(SET_ROW_ADDRESS)
        self.command(Ystart)          #page atart address
        self.command(Yend - 1)           #page end address

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
        self.command(SET_COLUMN_ADDRESS)
        self.command(0)         #cloumn start address
        self.command(self.width - 1) #cloumn end address
        self.command(SET_ROW_ADDRESS)
        self.command(0)         #page atart address
        self.command(self.height - 1) #page end address
        for i in range(0, self.height):
            for j in range(0, self.width*2):
                self.data(pBuf[j + self.width*2*i])
        return

       
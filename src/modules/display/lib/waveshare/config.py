# /*****************************************************************************
# * | File        :	  config.py
# * | Author      :   Waveshare team
# * | Function    :   Hardware underlying interface,for Raspberry pi
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2020-06-17
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


import time
from smbus import SMBus
import spidev
import ctypes
from gpiozero import DigitalOutputDevice, DigitalInputDevice

Device_SPI = 0
Device_I2C = 1

class RaspberryPi:
    def __init__(self,spi=spidev.SpiDev(0,0),spi_freq=10000000,rst = 26,dc = 24,bl = 18,bl_freq=1000,i2c=None):
        self.INPUT = False
        self.OUTPUT = True
        
        self.SPEED  =spi_freq

        if(Device_SPI == 1):
            self.Device = Device_SPI
            self.spi = spi
            
        else :
            self.Device = Device_I2C
            self.address = 0x3c
            self.bus = SMBus(1)

        self.RST_PIN = self.gpio_mode(rst,self.OUTPUT)
        self.DC_PIN = self.gpio_mode(dc,self.OUTPUT)

    def delay_ms(self,delaytime):
        time.sleep(delaytime / 1000.0)

    def gpio_mode(self,Pin,Mode,pull_up = None,active_state = True):
        if Mode:
            return DigitalOutputDevice(Pin,active_high = True,initial_value =False)
        else:
            return DigitalInputDevice(Pin,pull_up=pull_up,active_state=active_state)

    def digital_write(self, Pin, value):
        if value:
            Pin.on()
        else:
            Pin.off()

    def digital_read(self, Pin):
        return Pin.value

    def spi_writebyte(self,data):
        self.spi.writebytes([data[0]])

    def i2c_writebyte(self,reg, value):
        self.bus.write_byte_data(self.address, reg, value)
    
    def module_init(self): 
        self.digital_write(self.RST_PIN,False)
        if(self.Device == Device_SPI):
            self.spi.max_speed_hz = self.SPEED
            self.spi.mode = 0b11  
        self.digital_write(self.DC_PIN,False)
        return 0

    def module_exit(self):
        if(self.Device == Device_SPI):
            self.spi.close()
        else :
            self.bus.close()
        self.digital_write(self.RST_PIN,False)
        self.digital_write(self.DC_PIN,False)

### END OF FILE ###

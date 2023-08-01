import time
import board
import busio
from rainbowio import colorwheel
from adafruit_seesaw import seesaw, neopixel

class i2cneopixel:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        try:
            ss = seesaw.Seesaw(i2c, addr=0x60)
        except:
            i2c.deinit()
            i2c = busio.I2C(board.SCL, board.SDA)
            ss = seesaw.Seesaw(i2c, addr=0x60)
        neo_pin = 15
        num_pixels = 7

        pixels = neopixel.NeoPixel(ss, neo_pin, num_pixels, brightness = 0.1)

        color_offset = 0
        
        

        while True:
            for i in range(num_pixels):
                rc_index = (i * 256 // num_pixels) + color_offset
                pixels[i] = colorwheel(rc_index & 255)
            # Set pixel to white
            #pixels[0] = (255, 255, 255)
            pixels.show()
            color_offset += 1
            time.sleep(0.01)
    
if __name__ == '__main__':
    i2cneopixel()
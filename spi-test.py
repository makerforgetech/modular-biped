import time
import board
import neopixel_spi as neopixel

NUM_PIXELS = 4
PIXEL_ORDER = neopixel.GRB
DELAY = 1

spi = board.SPI()

pixels = neopixel.NeoPixel_SPI(
    spi, NUM_PIXELS, brightness=0.1, auto_write=False, pixel_order=PIXEL_ORDER
)

print("All neopixels OFF")
pixels.fill((0,0,0))
pixels.show()
time.sleep(DELAY)

print("One neopixel red")
pixels[0] = (10,0,0)
pixels.show()
time.sleep(DELAY)

print("All neopixels green")
pixels.fill((0,10,0))
pixels.show()
time.sleep(DELAY)

print("All neopixels OFF")
pixels.fill((0,0,0))
pixels.show()
time.sleep(DELAY)

print("End of test")

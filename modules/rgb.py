import pigpio
from time import sleep

class RGB:
    def __init__(self, r, g, b, **kwargs):
        pi = kwargs.get('pi', pigpio.pi())
        self.r = r
        self.g = g
        self.b = b
        self.pi = pi
        pi.set_mode(r, pigpio.OUTPUT)
        pi.set_mode(g, pigpio.OUTPUT)
        pi.set_mode(b, pigpio.OUTPUT)

    def breathe(self, color, start=0, increment=2, lighter=True):
        while start >= 0:
            self.led(color, start)
            if lighter is True:
                start = start + increment
            else:
                start = start - increment
            if start > 100:
                lighter =  not lighter
                start = 100
                sleep(1)
            sleep(0.05)
        sleep(1)
        
    def reset(self):
        self.led(self.r, 0)
        self.led(self.g, 0)
        self.led(self.b, 0)
        
    def led(self, color, percent):
        self.pi.set_PWM_dutycycle(color, 255*(percent/100))

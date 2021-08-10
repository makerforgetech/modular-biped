import pigpio
import time

pi = pigpio.pi()
pi.set_mode(5, pigpio.OUTPUT)
pi.set_mode(6, pigpio.OUTPUT)
pi.set_mode(13, pigpio.OUTPUT)
pi.set_mode(12, pigpio.OUTPUT)

BLUE = 5
GREEN = 6
RED = 13

ENABLE = 12
pi.write(ENABLE, 1) # test for enable pin

def breathe(color, start, increment, lighter):
    while start >= 0:
        led(color, start)
        if lighter is True:
            start = start + increment
        else:
            start = start - increment
        if start > 100:
            lighter =  not lighter
            start = 100
            time.sleep(1)
        time.sleep(0.05)
    time.sleep(1)    

def led(color, percent):
    global pi
    pi.set_PWM_dutycycle(color, 255*(percent/100))

try:
    while True:
        breathe(BLUE, 0, 2, True)
        breathe(RED, 0, 2, True)
        breathe(GREEN, 0, 2, True)

except KeyboardInterrupt:
        led(RED, 0)
        led(GREEN, 0)
        led(BLUE, 0)
        pi.write(ENABLE, 0)
        
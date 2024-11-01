import curses
import os
import datetime
import pigpio
from time import sleep

# f = open("recordings/" + datetime.datetime.now().strftime("%I:%M:%S %B-%d-%Y") + ".json","w+")
tstart = datetime.datetime.now()

pi = pigpio.pi()
pi.set_mode(17, pigpio.OUTPUT)
pi.set_mode(27, pigpio.OUTPUT)

pi.set_servo_pulsewidth(17, 1560)
pi.set_servo_pulsewidth(27, 1560)
sleep(0.25)

INCREMENT = 70

MIN = 600
MAX = 2400

TILT_MIN = 1420
TILT_MAX = 1980

def set_servo(pi, servo, pwm):
    global MIN
    global MAX
    if pwm < MIN:
        pwm = MIN
    if pwm > MAX:
        pwm = MAX
    pi.set_servo_pulsewidth(servo, pwm)

def main(win):
    global f
    global INCREMENT
    global MIN
    global MAX
    global pi
    global TILT_MIN
    global TILT_MAX
    
    val = TILT_MIN
    
    while val < TILT_MAX:
        val = val + INCREMENT
        set_servo(pi, 17, val)
        set_servo(pi, 27, val)
        if val >= TILT_MAX:
            val = TILT_MIN
        sleep(0.5)


curses.wrapper(main)


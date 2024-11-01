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

pi.set_servo_pulsewidth(17, 1760)
pi.set_servo_pulsewidth(27, 1560)
sleep(0.25)

INCREMENT = 40

def set_servo(pi, servo, pwm):
    if pwm < 1280:
        pwm = 1280
    if pwm > 2050:
        pwm = 2050
    pi.set_servo_pulsewidth(servo, pwm)

def main(win):
    global f
    global INCREMENT
    win.nodelay(True)
    key = ""
    win.clear()
    win.addstr("Detected key:")
    while 1:
        try:
            key = win.getkey()
            win.clear()
            win.addstr("Detected key:")
            win.addstr(str(key))
            win.addstr("[")
            win.addstr(str(pi.get_servo_pulsewidth(17)))
            win.addstr(",")
            win.addstr(str(pi.get_servo_pulsewidth(27)))
            win.addstr("]")
            
            if key == 'KEY_UP':
                set_servo(pi, 17, pi.get_servo_pulsewidth(17)-INCREMENT)
            if key == 'KEY_DOWN':
                set_servo(pi, 17, pi.get_servo_pulsewidth(17)+INCREMENT)
            if key == 'KEY_LEFT':
                set_servo(pi, 27, pi.get_servo_pulsewidth(27)+INCREMENT)
            if key == 'KEY_RIGHT':
                set_servo(pi, 27, pi.get_servo_pulsewidth(27)-INCREMENT)

            # add key and time in microseconds since start of script
            # f.write(str({"k": key, "s": (datetime.datetime.now() - tstart).microseconds}) + ',')

            if key == os.linesep:
                break
        except Exception as e:
            # No input
            pass


curses.wrapper(main)


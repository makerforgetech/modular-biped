import pigpio
import time

pi = pigpio.pi()
pi.set_mode(18, pigpio.OUTPUT)
pi.set_mode(23, pigpio.OUTPUT)
pi.set_mode(24, pigpio.OUTPUT)

BLUE = 18
GREEN = 23
RED = 24

def led(color, percent):
    global pi
    pi.set_PWM_dutycycle(color, 255*(percent/100))

while True:
#   pi.write(RED,1)
   led(RED, 10)
   time.sleep(1)
   led(RED, 20)
   time.sleep(1)
   led(RED, 50)
   time.sleep(1)
   led(RED, 100)
   time.sleep(1)
   pi.write(RED,0)
   time.sleep(1)
   pi.write(GREEN,1)
   time.sleep(1)
   pi.write(GREEN,0)
   time.sleep(1)
   pi.write(BLUE,1)
   time.sleep(1)
   pi.write(BLUE,0)
   time.sleep(5)

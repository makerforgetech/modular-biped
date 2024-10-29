
import pigpio
from time import sleep
pi = pigpio.pi()

while True:
    pi.write(2, 0)
    print('off')
    sleep(5)
    pi.write(2, 1)
    print('on')
    sleep(5)
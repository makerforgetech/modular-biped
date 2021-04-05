from modules.arduinoserial import ArduinoSerial
from time import time, sleep
import subprocess
from pubsub import pub

# battery value logging
import datetime

class Battery:

    BATTERY_THRESHOLD = 670  # max 760 (12.6v), min 670 (10.5v)
    BATTERY_LOW = 690  # max 760 (12.6v), min 670 (10.5v)
    READING_INTERVAL = 60 # seconds

    def __init__(self, pin, serial, **kwargs):
        self.pin = pin
        self.serial = serial
        self.interval = time()
        pub.subscribe(self.loop, 'loop')

    def loop(self):
        if self.interval < time() - Battery.READING_INTERVAL:
            self.interval = time()
            if self.low_voltage():
                pub.sendMessage('led:all', 'red')
            if not self.safe_voltage():
                print("BATTERY WARNING! SHUTTING DOWN!")
                pub.sendMessage('exit')
                sleep(5)
                subprocess.call(['shutdown', '-h'], shell=False)

    def check(self):
        val =  self.serial.send(ArduinoSerial.DEVICE_PIN_READ, 0, 0)
        print('bat:' + str(val))
        with open('/home/pi/really-useful-robot/battery.csv', 'a') as fd:
            fd.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ', ' + str(val) + '\n')
        return val

    def low_voltage(self):
        if self.check() < Battery.BATTERY_LOW and len(self.readings) == Battery.MAX_READINGS:
            return True
        return False

    def safe_voltage(self):
        if self.check() < Battery.BATTERY_THRESHOLD and len(self.readings) == Battery.MAX_READINGS:
            return False
        return True

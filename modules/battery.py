from modules.arduinoserial import ArduinoSerial
from time import time, sleep
import subprocess
from pubsub import pub

# battery value logging
import datetime

class Battery:

    BATTERY_THRESHOLD = 670  # 760 (11.7v), min 670 (10.5v)
    BATTERY_LOW = 690
    READING_INTERVAL = 60 # seconds

    def __init__(self, pin, serial, **kwargs):
        self.pin = pin
        self.serial = serial
        pub.subscribe(self.loop, 'loop:60')
        self.path = kwargs.get('path', '/')

    def loop(self):
        val = self.check()
        if val == 0:
            pub.sendMessage('led:full', color='red')
            pub.sendMessage('log:error', msg="[Battery] Battery Read Error - Value: " + str(val))
            return
        if self.low_voltage(val):
            pub.sendMessage('led:full', color='red')
            if not self.safe_voltage(val):
                pub.sendMessage('log:critical', msg="[Battery] EMERGENCY SHUTDOWN! Value: " + str(val))
                pub.sendMessage('exit')
                sleep(5)
                subprocess.call(['shutdown', '-h'], shell=False)

    def check(self):
        val =  self.serial.send(ArduinoSerial.DEVICE_PIN_READ, 0, 0)
        pub.sendMessage('log', msg="[Battery] Reading: " + str(val))
        with open(self.path + '/battery.csv', 'a') as fd:
            fd.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ', ' + str(val) + '\n')
        return val

    def low_voltage(self, val):
        if val < Battery.BATTERY_LOW:
            return True
        return False

    def safe_voltage(self, val):
        if val < Battery.BATTERY_THRESHOLD:
            return False
        return True

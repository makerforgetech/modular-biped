from modules.network.arduinoserial import ArduinoSerial
from time import time, sleep
import subprocess
from pubsub import pub
import datetime

class Battery:
    def __init__(self, **kwargs):
        """
        Battery module to check battery voltage
        :kwarg pin: pin number for battery voltage on Arduino (A0 by default)
        :kwarg path: path to log file
        :kwarg logfile: name of log file
        :kwarg bat_max: maximum battery voltage
        :kwarg bat_min: minimum battery voltage
        :kwarg bat_low: low battery
        
        Following initialisation, pass instance of serial to this module's self.serial attribute
        
        """
        self.pin = kwargs.get('pin')
        self.path = kwargs.get('path', '/')
        self.serial = None # Set this once modules are initialised
        self.logfile = self.path + '/' + kwargs.get('logfile')
        self.battery = {
            'max': kwargs.get('bat_max'),
            'min': kwargs.get('bat_min'),
            'low': kwargs.get('bat_low')
        }
        
        pub.subscribe(self.loop, 'loop:60')

    def loop(self):
        val = self.check()
        if val == 0:
            pub.sendMessage('log:error', msg="[Battery] Battery Read Error - Value: " + str(val))
            return
        
        if val < self.battery['low']:
            pub.sendMessage('log:warning', msg="[Battery] Low Battery - Value: " + str(val))
            pub.sendMessage('battery', value='low')
            if val < self.battery['min']:
                pub.sendMessage('log:critical', msg="[Battery] Critical Battery - Value: " + str(val))
                pub.sendMessage('battery', value='critical')
                pub.sendMessage('exit')
                sleep(5)
                subprocess.call(['shutdown', '-h'], shell=False)
                
    def check(self):
        val =  self.serial.send(ArduinoSerial.DEVICE_PIN_READ, 0, 0)
        pub.sendMessage('log', msg="[Battery] Reading: " + str(val))
        if self.logfile:
            with open(self.logfile, 'a') as fd:
                fd.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ', ' + str(val) + '\n')
        return val

    def low_voltage(self, val):
        if val < self.battery['low']:
            return True
        return False

    def min_voltage(self, val):
        if val < self.battery['min']:
            return True
        return False

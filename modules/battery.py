from modules.arduinoserial import ArduinoSerial

# battery value logging
import datetime

class Battery:

    BATTERY_THRESHOLD = 670  # max 760 (12.6v), min 670 (10.5v)
    MAX_READINGS = 10

    def __init__(self, pin, serial, **kwargs):
        self.pin = pin
        self.readings = []
        self.serial = serial

    def check(self):
        val = self.serial.send(ArduinoSerial.DEVICE_PIN_READ, 0, 0)
        self.readings.append(val)
        if len(self.readings) > Battery.MAX_READINGS:
            self.readings.pop(0)

        avg = sum(self.readings) / len(self.readings)

        # print('bat:' + str(avg))
        # with open('/home/pi/really-useful-robot/battery.csv', 'a') as fd:
        #     fd.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ', ' + str(val) + '\n')
        return avg

    def safe_voltage(self):
        if self.check() < Battery.BATTERY_THRESHOLD and len(self.readings) == Battery.MAX_READINGS:
            return False
        return True

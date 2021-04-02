from modules.arduinoserial import ArduinoSerial

# battery value logging
import datetime

class Battery:

    BATTERY_THRESHOLD = -60  # max 100 (12.3v), min -60 (8.8v)
    MAX_READINGS = 10

    def __init__(self, pin, serial, **kwargs):
        self.pin = pin
        self.readings = []
        self.serial = serial

    def check(self):
        val = self.serial.send(ArduinoSerial.DEVICE_PIN_READ, 0, 0)
        # @todo this just stops the servos from working properly. This whole thing is a bit of a mess
        # escape = 5
        # while val == ArduinoSerial.ORDER_RECEIVED and escape > 0:
        #     escape = escape-1
        #     val = self.serial.send(ArduinoSerial.DEVICE_PIN_READ, 0, 0)
        if val == ArduinoSerial.ORDER_RECEIVED:
            return 0
        self.readings.append(val)
        if len(self.readings) > Battery.MAX_READINGS:
            self.readings.pop(0)

        avg = sum(self.readings) / len(self.readings)

        print('bat:' + str(avg))
        with open('/home/pi/really-useful-robot/battery.csv', 'a') as fd:
            fd.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ', ' + str(val) + '\n')
        return avg

    def safe_voltage(self):
        if self.check() < Battery.BATTERY_THRESHOLD and len(self.readings) == Battery.MAX_READINGS:
            return False
        return True

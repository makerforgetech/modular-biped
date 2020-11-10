from modules.arduinoserial import ArduinoSerial

class Battery:

    BATTERY_THRESHOLD = 40
    MAX_READINGS = 10

    def __init__(self, pin, serial, **kwargs):
        self.pin = pin
        self.readings = []
        self.serial = serial

    def check(self):
        val = self.serial.send(ArduinoSerial.DEVICE_PIN_READ, 0, None)
        if val == 5.0:
            return 0
        self.readings.append(val)
        if len(self.readings) > Battery.MAX_READINGS:
            self.readings.pop(0)

        avg = sum(self.readings) / len(self.readings)

        # print(val)
        # print(self.readings)
        print(avg)
        return avg

    def safe_voltage(self):
        if self.check() < Battery.BATTERY_THRESHOLD and len(self.readings) == Battery.MAX_READINGS:
            return False
        return True

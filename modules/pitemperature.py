import os


class PiTemperature:
    WARNING_TEMP = 80

    @staticmethod
    def read():
        temp = os.popen("vcgencmd measure_temp").readline()
        return temp.replace("temp=", "").replace("'C", "").strip()

    @staticmethod
    def hot():
        return PiTemperature.read() >= PiTemperature.WARNING_TEMP

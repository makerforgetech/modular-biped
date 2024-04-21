import os
from pubsub import pub

class PiTemperature:
    WARNING_TEMP = 80
    THROTTLED_TEMP = 85
    AVG_TEMP = 50
    MIN_TEMP = 15

    def __init__(self):
        pub.subscribe(self.monitor, 'loop:60')

    @staticmethod
    def read():
        temp = os.popen("vcgencmd measure_temp").readline()
        return temp.replace("temp=", "").replace("'C", "").strip()

    def monitor(self):
        val = self.read()
        pub.sendMessage('log', msg='[TEMP] ' + val)
        val = float(val)
        if val >= PiTemperature.THROTTLED_TEMP:
            pub.sendMessage('led', identifiers='status2', color='red') # WARNING
        else:
            pub.sendMessage('led', identifiers='status2', color=self.map_range(round(val)), gradient='br')  # right


    def map_range(self, value):
        # Cap range for LED
        if value > PiTemperature.WARNING_TEMP:
            value = PiTemperature.WARNING_TEMP
        if value < PiTemperature.AVG_TEMP:
            value = PiTemperature.AVG_TEMP

        # translate range (STARTUP_TEMP to WARNING_TEMP) to (100 to 0) (green is cool, red is hot)
        OldRange = (PiTemperature.MIN_TEMP - PiTemperature.WARNING_TEMP)
        NewRange = (100 - 0)
        val = (((value - PiTemperature.WARNING_TEMP) * NewRange) / OldRange) + 0
        return val
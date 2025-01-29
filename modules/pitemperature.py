import os
from modules.base_module import BaseModule

class PiTemperature(BaseModule):
    WARNING_TEMP = 80
    THROTTLED_TEMP = 85
    AVG_TEMP = 50
    MIN_TEMP = 15
    
    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('system/loop/60', self.monitor)

    @staticmethod
    def read():
        temp = os.popen("vcgencmd measure_temp").readline()
        return temp.replace("temp=", "").replace("'C", "").strip()

    def monitor(self):
        val = self.read()
        self.publish('log', '[TEMP] ' + val)
        self.publish('system/temperature', val)
        float_val = float(val)
        if float_val > PiTemperature.THROTTLED_TEMP:
            self.publish('log/critical', '[TEMP] ' + val)
        elif float_val > PiTemperature.WARNING_TEMP:
            self.publish('log/warning', '[TEMP] ' + val)

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

import os, sys
import threading
import time
from modules.base_module import BaseModule

class PiTemperature(BaseModule):
    WARNING_TEMP = 80
    THROTTLED_TEMP = 85
    SHUTDOWN_TEMP = 90
    AVG_TEMP = 50
    MIN_TEMP = 15
    MONITOR_INTERVAL = 60  # seconds
    
    def __init__(self):
        self.debug = False
    
    def setup_messaging(self):
        """No longer subscribes to system/loop/60; starts background thread instead."""
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._monitor_thread, daemon=True)
        self._thread.start()
        self._start_time = time.time() # For debug
        self._min_temp = None # For debug
        self._max_temp = None # For debug

    def _monitor_thread(self):
        while not getattr(self, '_stop_event', threading.Event()).is_set():
            self.monitor()
            time.sleep(PiTemperature.MONITOR_INTERVAL)


    @staticmethod
    def read():
        temp = os.popen("vcgencmd measure_temp").readline()
        return temp.replace("temp=", "").replace("'C", "").strip()

    def monitor(self):
        val = self.read()
        # get degrees celsius symbol
        outputval = val + u"\u00b0" + "C"
        self.publish('system/temperature', value=val)
        float_val = float(val)
        if self.debug:
            if self._min_temp is None or float_val < self._min_temp:
                self._min_temp = float_val
            if self._max_temp is None or float_val > self._max_temp:
                self._max_temp = float_val
            self.log(f'Temperature read: {outputval}, run time: {round((time.time() - self._start_time) / 60)} minutes. Min/Max temps: [{self._min_temp}, {self._max_temp}]')
        # exit python script if temperature is above shutdown temp
        if float_val > PiTemperature.SHUTDOWN_TEMP:
            self.log(f'Temperature is too high exiting script: {outputval}', 'critical')
            sys.exit(1)
        elif float_val > PiTemperature.THROTTLED_TEMP:
            self.log(f'Temperature is critical: {outputval}', 'critical')
            self.publish('system/sleep', requestor=type(self).__name__) # Sleep system to reduce temperature
        elif float_val > PiTemperature.WARNING_TEMP:
            self.log(f'Temperature is high: {outputval}', 'warning')
            self.publish('system/throttle', requestor=type(self).__name__) # Thottle system to reduce temperature
        else:
            self.log(f'Temperature: {outputval}', 'debug')
            self.publish('system/wake', requestor=type(self).__name__)

    def stop(self):
        if hasattr(self, '_stop_event'):
            self._stop_event.set()
        if hasattr(self, '_thread'):
            self._thread.join(timeout=2)

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
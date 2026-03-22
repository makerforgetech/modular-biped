from gpiozero import MotionSensor
from time import time, sleep
from modules.base_module import BaseModule

class Motion(BaseModule):
    def __init__(self, **kwargs):
        """
        Motion Sensor class
        :param kwargs: pin
        
        Install: pip install gpiozero
        
        Polls the sensor in a background thread every second.
        Publishes 'gpio/motion' when motion detected.
        
        Example:
        self.subscribe('motion', callback)
        """
        import threading
        self.pin = kwargs.get('pin')
        self.value = None
        self.sensor = MotionSensor(self.pin)
        self._stop_thread = False
        self._thread = threading.Thread(target=self._poll_sensor, daemon=True)
        
        self.last_motion = None
        if kwargs.get('test_on_boot'):
            self.test()
            
    def setup_messaging(self):
        """No longer subscribes to system/loop/1; polling is handled by thread."""
        self._thread.start()
        self.log("Starting motion sensor polling")

    def _poll_sensor(self):
        self.log("Starting motion sensor polling thread")
        while not self._stop_thread:
            if self.read():
                self.last_motion = time()
            val = round(time() - self.last_motion) if self.last_motion else None
            self.publish('gpio/motion', value=val)
            # self.log(f"Seconds since last motion: {val}")
            sleep(1)

    def read(self):
        self.value = self.sensor.motion_detected
        return self.value
    
    def test(self):
        while True:
            print(self.read())
            sleep(1)
    def stop(self):
        """Stop the polling thread if needed."""
        self._stop_thread = True
        if hasattr(self, '_thread'):
            self._thread.join(timeout=2)

    # def watch(self, edge, callback):
    #     """
    #     :param edge: pigpio.EITHER_EDGE, pigpio.FALLING_EDGE, pigpio.RISING_EDGE
    #     :param callback: method to call when change detected
    #     """
    #     return self.pi.callback(self.pin, edge, callback)

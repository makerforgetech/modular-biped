from gpiozero import MotionSensor
from time import sleep
from modules.base_module import BaseModule

class Sensor(BaseModule):
    def __init__(self, **kwargs):
        """
        Sensor class
        :param kwargs: pin
        
        Install: pip install gpiozero
        
        Subscribes to 'loop:1' to read sensor
        Publishes 'motion' when motion detected
        
        Example:
        self.subscribe('motion', callback)
        
        """
        self.pin = kwargs.get('pin')
        self.value = None
        self.sensor = MotionSensor(self.pin)
        
        if kwargs.get('test_on_boot'):
            self.test()
            
    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('system/loop/1', self.loop)

    def loop(self):
        if self.read():
            self.publish('motion')

    def read(self):
        self.value = self.sensor.motion_detected
        return self.value
    
    def test(self):
        while True:
            print(self.read())
            sleep(1)

    # def watch(self, edge, callback):
    #     """
    #     :param edge: pigpio.EITHER_EDGE, pigpio.FALLING_EDGE, pigpio.RISING_EDGE
    #     :param callback: method to call when change detected
    #     """
    #     return self.pi.callback(self.pin, edge, callback)

from gpiozero import MotionSensor
from pubsub import pub
from time import sleep
class Sensor:
    def __init__(self, **kwargs):
        """
        Sensor class
        :param kwargs: pin
        
        Install: pip install gpiozero
        
        Subscribes to 'loop:1' to read sensor
        Publishes 'motion' when motion detected
        
        Example:
        pub.subscribe(handleMotion, 'motion')
        
        """
        self.pin = kwargs.get('pin')
        self.value = None
        self.sensor = MotionSensor(self.pin)
        pub.subscribe(self.loop, 'loop:1')
        
        if kwargs.get('test_on_boot'):
            self.test()

    def loop(self):
        if self.read():
            pub.sendMessage('motion')

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

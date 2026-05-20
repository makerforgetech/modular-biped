from gpiozero import LED
from time import sleep
from modules.base_module import BaseModule

class Laser(BaseModule):
    def __init__(self, **kwargs):
        """
        Sensor class
        :param kwargs: pin
        
        Install: pip install gpiozero
        
        """
        self.pin = kwargs.get('pin')
        self.laser = LED(self.pin)
        self.laser.off()
        self.state = kwargs.get('state', False)
        self.activate(self.state)
        
        if kwargs.get('test_on_boot'):
            self.test()
            
    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('gpio/laser', self.activate)  # Subscribe to toggle laser
        self.subscribe('gpio/laser/toggle', self.toggle)

    def activate(self, state):
        """
        Activate the laser with the given state.
        :param state: True to turn on, False to turn off
        """
        if state:
            self.laser.on()
        else:
            self.laser.off()
        self.state = state

    def toggle(self):
        if self.state:
            self.laser.on()
        else:
            self.laser.off()
        self.state = not self.state  # Toggle state
    
    def test(self):
        while True:
            self.toggle()
            print(f"Laser state: {'ON' if self.laser.is_lit else 'OFF'}")
            sleep(1)

    # def watch(self, edge, callback):
    #     """
    #     :param edge: pigpio.EITHER_EDGE, pigpio.FALLING_EDGE, pigpio.RISING_EDGE
    #     :param callback: method to call when change detected
    #     """
    #     return self.pi.callback(self.pin, edge, callback)

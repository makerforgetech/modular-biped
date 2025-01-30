import json
import os.path
from time import sleep
from gpiozero import LED
from modules.base_module import BaseModule

class Animate(BaseModule):
    def __init__(self, **kwargs):
        """
        Animation module to move servos in sequence
        :kwarg path: path to animation files
        
        Install: pip install gpiozero
        
        Subscribes to 'animate' to start an animation
        - Argument: action (string) - name of animation file
        
        Example:
        self.publish('animate', action='head_nod')
        """
        self.path = kwargs.get('path', os.path.dirname(os.path.realpath(__file__)) + '/../animations') + '/'

    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('animate', self.animate)

    def animate(self, action):
        """
        Move pan and tilt servos in sequence defined by given file
        :param filename: animation file in path specified in init
        """
        file = self.path + action + '.json'
        if not os.path.isfile(file):
            raise ValueError('Animation does not exist: ' + action)
        
        self.log(f"Animating: {action}")

        with open(file, 'r') as f:
            parsed = json.load(f)

        for step in parsed:
            cmd = list(step.keys())[0]
            args = list(step.values())
            if 'servo:' in cmd:
                self.publish(cmd, percentage=args[0])
            elif 'sleep' == cmd:
                sleep(args[0])
            elif 'animate' == cmd:
                self.publish(cmd, action=args[0])
            elif 'led/' in cmd:
                self.publish(cmd, color=args[0])
            elif 'speak' == cmd:
                self.publish(cmd, message=args[0])
            elif 'pin' in cmd:
                led = LED(args[0])
                if 'pin:high' == cmd:
                    led.on()
                else:
                    led.off()

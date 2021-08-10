import json
import os.path
from pubsub import pub
from time import sleep


class Animate:
    def __init__(self, **kwargs):
        self.path = kwargs.get('path', os.path.dirname(os.path.realpath(__file__)) + '/../animations') + '/'
        pub.subscribe(self.animate, "animate")

    def animate(self, action):
        """
        Move pan and tilt servos in sequence defined by given file
        :param filename: animation file in path specified in init
        """
        file = self.path + action + '.json'
        if not os.path.isfile(file):
            raise ValueError('Animation does not exist: ' + action)

        with open(file, 'r') as f:
            parsed = json.load(f)

        for step in parsed:
            cmd = list(step.keys())[0]
            args = list(step.values())
            if 'servo:' in cmd:
                pub.sendMessage(cmd, percentage=args[0])
            elif 'sleep' == cmd:
                sleep(args[0])
            elif 'animate' == cmd:
                pub.sendMessage(cmd, action=args[0])
            elif 'led:' in cmd:
                pub.sendMessage(cmd, color=args[0])
            elif 'speak' == cmd:
                pub.sendMessage(cmd, message=args[0])

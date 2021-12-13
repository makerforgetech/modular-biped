from random import randint, randrange
from pubsub import pub
from time import sleep, localtime

from modules.config import Config

class Random:
    def __init__(self, state):
        self.state = state  # the personality instance
        pub.subscribe(self.behave_minute, 'loop:minute')

    def behave_minute(self):
        if not self.state.is_resting() and randrange(5) is 1:
            # Random action to simulate behaviour, then reset. WIP.
            actions = ['sleep', 'look_up', 'look_down', 'head_shake', 'head_nod', 'neck_forward', 'head_right',
                       'head_left', 'speak']
            action = actions[randrange(len(actions)-1)]
            pub.sendMessage('log', msg='[Personality] Random action: ' + str(action))
            if action is 'speak':
                pub.sendMessage('speak', message='hi')
            else:
                pub.sendMessage('animate', action=action)
            sleep(randrange(3))
            pub.sendMessage('animate', action="wake")
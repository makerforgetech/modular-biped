from pubsub import pub
from time import sleep, localtime
from modules.config import Config
from random import randrange

class Respond:

    def __init__(self, state):
        self.state = state  # the personality instance
        pub.subscribe(self.speech, 'speech')

    def speech(self, msg):
        if self.state.is_resting():
            return

        action = None
        if 'are you sure' in msg:
            action = 'head_nod'
        if 'you like' in msg:
            actions = ['head_shake', 'head_nod', 'speak']
            action = actions[randrange(len(actions) - 1)]

        if action:
            pub.sendMessage('log', msg='[Personality] Respond action: ' + str(action))
            if action is 'speak':
                pub.sendMessage('speak', message=msg)
            else:
                pub.sendMessage('animate', action=action)
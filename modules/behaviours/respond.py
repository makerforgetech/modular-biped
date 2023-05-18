from pubsub import pub
from time import sleep, localtime
from modules.config import Config
from random import randrange

class Respond:

    def __init__(self, state):
        self.state = state  # the personality instance
        pub.subscribe(self.speech, 'speech')
        pub.subscribe(self.tracking, 'tracking:match')

    def speech(self, msg):
        if self.state.is_resting():
            return

        action = None
        if 'are you sure' in msg:
            action = 'head_nod'
        if 'you like' in msg:
            actions = ['head_shake', 'head_nod', 'speak']
            action = actions[abs(hash(msg.split('like ')[1])) % len(actions)-1] # choose from the number of actions by hashing the item, so the answer is always the same
            # action = actions[randrange(len(actions) - 1)]

        if action:
            pub.sendMessage('log', msg='[Personality] Respond action: ' + str(action))
            if action is 'speak':
                pub.sendMessage('speak', message=msg)
            else:
                pub.sendMessage('animate', action=action)

    def tracking(self, largest, screen):
        """
        Show the position of the largest match in the eye LEDs
        """
        if largest is None:
            return

        (x, y, w, h) = largest
        if x + (w / 2) < (screen[0] / 2) - 60:
            pub.sendMessage('led', identifiers=['left', 'middle'], color='off')
            pub.sendMessage('led', identifiers='right', color='green')
        elif x + (w / 2) > (screen[0] / 2) + 60:
            pub.sendMessage('led', identifiers=['right', 'middle'], color='off')
            pub.sendMessage('led', identifiers='left', color='green')
        else:
            pub.sendMessage('led', identifiers=['left', 'right'], color='off')
            pub.sendMessage('led', identifiers='middle', color='green')
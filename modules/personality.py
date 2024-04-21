from random import randint
from time import sleep, localtime
from pubsub import pub
from datetime import datetime, timedelta

from modules.config import Config

from modules.behaviours.dream import Dream
from modules.behaviours.faces import Faces
from modules.behaviours.motion import Motion
from modules.behaviours.boredom import Boredom
from modules.behaviours.feel import Feel
from modules.behaviours.sleep import Sleep
from modules.behaviours.respond import Respond
from modules.behaviours.objects import Objects
from modules.behaviours.sentiment import Sentiment

from types import SimpleNamespace

"""
This class dictates the behaviour of the robot, subscribing to various input events (face matches or motion)
and triggering animations as a result of those behaviours (or lack of) 

It also stores the current 'state of mind' of the robot, so that we can simulate boredom and other emotions based
on the above stimulus.

To update the personality status from another module, publish to the 'behaviour' topic one of the defined INPUT_TYPE constants:
from pubsub import pub
pub.sendMessage('behaviour', type=Personality.INPUT_TYPE_FUN)
"""

class Personality:


    def __init__(self, **kwargs):
        self.mode = kwargs.get('mode', Config.MODE_LIVE)
        self.state = Config.STATE_SLEEPING
        self.eye = 'blue'

        pub.subscribe(self.loop, 'loop:1')
        pub.subscribe(self.process_sentiment, 'sentiment')
        
        behaviours = { 'boredom': Boredom(self),
                       'dream': Dream(self),
                       'faces': Faces(self),
                       'motion': Motion(self),
                       'sleep': Sleep(self),
                       'feel': Feel(self),
                       'objects': Objects(self),
                       'respond': Respond(self),
                       'sentiment': Sentiment(self)}

        self.behaviours = SimpleNamespace(**behaviours)

    def loop(self):
        # pub.sendMessage('speech', msg="Hello, I am happy") # for testing sentiment responses
        if not self.is_asleep() and not self.behaviours.faces.face_detected and not self.behaviours.motion.is_motion() and not self.behaviours.objects.is_detected:
            self.set_eye('red')

        if self.state == Config.STATE_ALERT and self.lt(self.behaviours.faces.last_face, self.past(2*60)) and self.lt(self.behaviours.objects.last_detection, self.past(2*60)):
            # reset to idle position after 2 minutes inactivity
            pub.sendMessage('animate', action="wake")
            self.set_state(Config.STATE_IDLE)

    def process_sentiment(self, score):
        pub.sendMessage('log', msg="[Personality] Sentiment: " + str(score))
        if score > 0:
            pub.sendMessage('piservo:move', angle=0)
        else:
            pub.sendMessage('piservo:move', angle=40)
        
    def set_eye(self, color):
        if self.eye == color:
            return
        # pub.sendMessage('led', identifiers=['left', 'right'], color='off')
        pub.sendMessage('led:eye', color=color)
        self.eye = color

    def set_state(self, state):
        if self.state == state:
            return

        pub.sendMessage('log', msg="[Personality] State: " + str(state))
        if state == Config.STATE_SLEEPING:
            pub.sendMessage("sleep")
            pub.sendMessage("animate", action="sleep")
            pub.sendMessage("animate", action="sit")
            pub.sendMessage("led:off")
            pub.sendMessage("led", identifiers=['status1'], color="off")
            pub.sendMessage('piservo:move', angle=0)
        elif state == Config.STATE_RESTING:
            pub.sendMessage('rest')
            pub.sendMessage("animate", action="sit")
            pub.sendMessage("animate", action="sleep")
            self.set_eye('blue')
            pub.sendMessage("led", identifiers=['status1'], color="red")
            pub.sendMessage('piservo:move', angle=-40)
        elif state == Config.STATE_IDLE:
            if self.state == Config.STATE_RESTING or self.state == Config.STATE_SLEEPING:
                pub.sendMessage('wake')
                pub.sendMessage('animate', action="wake")
            pub.sendMessage('animate', action="sit")
            pub.sendMessage("led", identifiers=['status1'], color="green")
            pub.sendMessage('piservo:move', angle=-20)
            self.set_eye('blue')
        elif state == Config.STATE_ALERT:
            if self.state == Config.STATE_RESTING or self.state == Config.STATE_SLEEPING:
                pub.sendMessage('wake')
                pub.sendMessage('animate', action="wake")
            # pub.sendMessage('animate', action="stand")
            pub.sendMessage('piservo:move', angle=0)
            pub.sendMessage("led", identifiers=['status1'], color="blue")
        self.state = state

    def is_asleep(self):
        return self.state == Config.STATE_SLEEPING

    def is_resting(self):
        return self.state == Config.STATE_SLEEPING or self.state == Config.STATE_RESTING

    def lt(self, date, compare):
        return date is None or date < compare

    def past(self, seconds):
        return datetime.now() - timedelta(seconds=seconds)
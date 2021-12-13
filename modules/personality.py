from random import randint
from time import sleep, localtime
from pubsub import pub
from datetime import datetime, timedelta

from modules.config import Config

from modules.behaviours.dream import Dream
from modules.behaviours.faces import Faces
from modules.behaviours.motion import Motion
from modules.behaviours.random import Random
from modules.behaviours.feel import Feel

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
    STATE_SLEEPING = 0
    STATE_RESTING = 1
    STATE_IDLE = 2
    STATE_ALERT = 3

    NIGHT_HOURS = [22, 8] # night start and end. Will not wake during this time

    def __init__(self, **kwargs):
        self.mode = kwargs.get('mode', Config.MODE_LIVE)
        self.state = Personality.STATE_SLEEPING
        self.eye = 'blue'

        pub.subscribe(self.loop, 'loop:1')
        pub.subscribe(self.minute_loop, 'loop:60')
        pub.subscribe(self.nightly_loop, 'loop:nightly')


        self.behaviours = {'random': Random(self),
                           'dream': Dream(self),
                           'faces': Faces(self),
                           'motion': Motion(self),
                           'sleep': Sleep(self),
                           'feel': Feel(self)}

    def loop(self):
        if not self.is_asleep() and not self.behaviours.faces.face_detected and self.behaviours.motion.last_motion < self.past(2):
            self.set_eye('red')

        if self.state == Personality.STATE_ALERT and self.lt(self.behaviours.faces.last_face, self.past(2*60)):
            # reset to idle position after 2 minutes inactivity
            pub.sendMessage('animate', action="wake")
            self.set_state(Personality.STATE_IDLE)

    def set_eye(self, color):
        if self.eye == color:
            return
        pub.sendMessage('led:eye', color=color)
        self.eye = color

    def set_state(self, state):
        if self.state == state:
            return

        pub.sendMessage('log', msg="[Personality] State: " + str(state))
        if state == Personality.STATE_SLEEPING:
            pub.sendMessage("sleep")
            pub.sendMessage("animate", action="sleep")
            pub.sendMessage("animate", action="sit")
            pub.sendMessage("power:exit")
            pub.sendMessage("led:off")
        elif state == Personality.STATE_RESTING:
            pub.sendMessage('rest')
            pub.sendMessage("animate", action="sit")
            pub.sendMessage("animate", action="sleep")
            pub.sendMessage("power:exit")
            self.set_eye('blue')
        elif state == Personality.STATE_IDLE:
            if self.state == Personality.STATE_RESTING:
                pub.sendMessage('wake')
                pub.sendMessage('animate', action="wake")
            pub.sendMessage('animate', action="sit")
            self.set_eye('blue')
        elif state == Personality.STATE_ALERT:
            pass
            # pub.sendMessage('animate', action="stand")
        self.state = state

    def is_asleep(self):
        return self.state == Personality.STATE_SLEEPING

    def is_resting(self):
        return self.state == Personality.STATE_SLEEPING or self.state == Personality.STATE_RESTING

    @staticmethod
    def is_night():
        t = localtime()
        if Personality.NIGHT_HOURS[1] < t.tm_hour < Personality.NIGHT_HOURS[0]:
            return False
        return True

    def lt(self, date, compare):
        return date is None or date < compare

    def past(self, seconds):
        return datetime.now() - timedelta(seconds=seconds)
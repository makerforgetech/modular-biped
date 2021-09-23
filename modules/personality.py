from random import randint, randrange
from time import sleep, localtime
from pubsub import pub
from datetime import datetime, timedelta

from modules.config import Config

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
    INPUT_TYPE_INTERESTING = 0
    INPUT_TYPE_SCARY = 1
    INPUT_TYPE_FUN = 1
    INPUT_TYPE_STARTLING = 1

    BEHAVE_INTERVAL = 2
    OUTPUT_INTERVAL = 30
    SLEEP_TIMEOUT =  2 * 60
    REST_TIMEOUT = 30

    STATE_SLEEPING = 0
    STATE_RESTING = 1
    STATE_IDLE = 2
    STATE_ALERT = 3

    NIGHT_HOURS = [22, 8] # night start and end. Will not wake during this time

    def __init__(self, **kwargs):
        self.mode = kwargs.get('mode', Config.MODE_LIVE)
        self.happiness = 50
        self.contentment = 50
        self.attention = 50
        self.wakefulness = 100

        self.last_behave = datetime.now()
        self.last_output = datetime.now()
        self.last_motion = datetime.now()
        self.last_face = None
        self.last_face_name = None
        self.face_detected = None

        self.state = Personality.STATE_SLEEPING
        self.eye = 'blue'
        self.state_change = datetime.now()

        pub.subscribe(self.loop, 'loop:1')
        pub.subscribe(self.minute_loop, 'loop:60')
        pub.subscribe(self.nightly_loop, 'loop:nightly')
        pub.subscribe(self.input, 'behaviour')
        pub.subscribe(self.face, 'vision:detect:face')
        pub.subscribe(self.noface, 'vision:nomatch')
        pub.subscribe(self.motion, 'motion')

    def loop(self):
        self.attention += randint(-20,20)
        self.happiness += randint(-2, 2)
        self.wakefulness -= randint(0, 3)
        self.contentment -= randint(0, 3)
        self.handle_sleep()

        if not self._asleep() and not self.face_detected and self.last_motion < self._past(2):
            self.set_eye('red')

        if self.state == Personality.STATE_ALERT and self._lt(self.last_face, self._past(2*60)):
            # reset to idle position after 2 minutes inactivity
            pub.sendMessage('animate', action="wake")
            self.set_state(Personality.STATE_IDLE)

    def nightly_loop(self):
        # This will attempt to process anything in the 'matches/verified' directory, or return if nothing to process
        if self._asleep() and Personality.is_night():
            pub.sendMessage('log', msg="[Personality] Training model")
            pub.sendMessage('vision:train')

    def minute_loop(self):
        if not self._resting() and randrange(5) is 1:
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

    def handle_sleep(self):
        if self._asleep():
            sleep(5)

        # if sleeping and motion detected in the last X seconds, then wake (during the day)
        if self._asleep() and not Personality.is_night() and self.last_motion > self._past(10):
            self.set_state(Personality.STATE_RESTING)

        # if not sleeping and motion not detected for SLEEP_TIMEOUT, sleep
        if not self._asleep() and self._lt(self.last_motion, self._past(Personality.SLEEP_TIMEOUT)):
            self.set_state(Personality.STATE_SLEEPING)

        # if not resting and faces not detected for REST_TIMEOUT, rest
        if not self._resting() and self._lt(self.last_face, self._past(Personality.REST_TIMEOUT)):
            self.set_state(Personality.STATE_RESTING)

    def motion(self):
        self.last_motion = datetime.now()
        if not self.face_detected and self._lt(self.last_face, self._past(2)):
            self.set_eye('blue')

    def noface(self):
        pub.sendMessage('log:info', msg='[Personality] No face matches found')
        self.face_detected = False

    def face(self, name):
        pub.sendMessage('log:info', msg='[Personality] Face detected: ' + str(name))
        self.face_detected = True
        self.last_face = datetime.now()
        self.set_state(Personality.STATE_IDLE)
        if name == 'Unknown':
            self.set_eye('purple')
        else:
            # self.set_state(Personality.STATE_ALERT)  # This overrides the tracking so we can't trigger this here
            self.set_eye('green')
            if self.last_face_name != name:
                pub.sendMessage('speak', message=name)

        if name != 'Unknown':
            self.last_face_name = name

    def behave(self):
        if self.last_behave > self._past(Personality.BEHAVE_INTERVAL):
            return

        self.last_behave = datetime.now()

        feelings = []
        if self.happiness < 10:
            feelings.append('sad')
        if self.attention < 30:
            feelings.append('bored')
        if self.wakefulness < 20:
            feelings.append('tired')
        if self.wakefulness < 0:
            feelings.append('asleep')
        if self.contentment < 20:
            feelings.append('restless')
        if len(feelings) == 0:
            feelings.append('ok')
        return feelings

    def set_eye(self, color):
        if self.eye == color:
            return
        pub.sendMessage('led:eye', color=color)
        self.eye = color

    def set_state(self, state):
        if self.state == state:
            return

        pub.sendMessage('log', msg="[Personality] State: " + str(state))
        self.state_change = datetime.now()
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

    def _asleep(self):
        return self.state == Personality.STATE_SLEEPING

    def _resting(self):
        return self.state == Personality.STATE_SLEEPING or self.state == Personality.STATE_RESTING

    def input(self, type):
        if type == Personality.INPUT_TYPE_INTERESTING:
            self.attention = 100
            self.happiness += 30
            self.wakefulness += 30
            self.contentment += 30
        if type == Personality.INPUT_TYPE_SCARY:
            self.attention = 100
            self.happiness = 20
            self.wakefulness += 50
            self.contentment -= 30
        if type == Personality.INPUT_TYPE_FUN:
            self.attention = 100
            self.happiness = 100
            self.wakefulness += 50
            self.contentment += 50
        if type == Personality.INPUT_TYPE_STARTLING:
            self.attention = 100
            self.happiness -= 40
            self.wakefulness += 50
            self.contentment -= 10

    def output(self):
        print('happiness: ' + str(self.happiness))
        print('attention: ' + str(self.attention))
        print('wakefulness: ' + str(self.wakefulness))
        print('contentment: ' + str(self.contentment))

    @staticmethod
    def is_night():
        t = localtime()
        if Personality.NIGHT_HOURS[1] < t.tm_hour < Personality.NIGHT_HOURS[0]:
            return False
        return True

    def _lt(self, date, compare):
        return date is None or date < compare

    def _past(self, seconds):
        return datetime.now() - timedelta(seconds=seconds)
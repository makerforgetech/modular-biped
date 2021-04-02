from random import randint
from time import sleep
from pubsub import pub
import datetime

"""
To update the personality status, publish to the 'behaviour' topic one of the defined INPUT_TYPE constants:

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
    SLEEP_TIMEOUT = 5 * 60

    def __init__(self, **kwargs):
        self.happiness = 50
        self.contentment = 50
        self.attention = 50
        self.wakefulness = 100

        self.do_output = kwargs.get('debug', False)

        self.last_behave = datetime.datetime.now()
        self.last_output = datetime.datetime.now()
        self.last_motion = datetime.datetime.now()
        self.sleeping = False

        pub.subscribe(self.input, 'behaviour')
        pub.subscribe(self.face, 'vision:detect:face')
        pub.subscribe(self.motion, 'motion')

    def cycle(self):
        self.attention += randint(-20,20)
        self.happiness += randint(-2, 2)
        self.wakefulness -= randint(0, 3)
        self.contentment -= randint(0, 3)
        self.handle_sleep()

    def handle_sleep(self):
        # if sleeping and motion detected in the last 5 seconds, then wake
        if self.sleeping and self.last_motion is not None and self.last_motion > datetime.datetime.now() - datetime.timedelta(
                seconds=5):
            if self.do_output:
                print('WAKING')
            self.sleeping = False
            pub.sendMessage('wake')
            pub.sendMessage('led:eye', color="blue")
            pub.sendMessage("animate", action="wake")
            pub.sendMessage("animate", action="stand")

        if self.do_output:
            print(self.sleeping)
            if self.last_motion is not None:
                print(self.last_motion)
                print(datetime.datetime.now() - datetime.timedelta(seconds=Personality.SLEEP_TIMEOUT))
                print(
                    self.last_motion < datetime.datetime.now() - datetime.timedelta(seconds=Personality.SLEEP_TIMEOUT))

        # if not sleeping and motion not detected for SLEEP_TIMEOUT, sleep
        if not self.sleeping and self.last_motion is not None and self.last_motion < datetime.datetime.now() - datetime.timedelta(
                seconds=Personality.SLEEP_TIMEOUT):
            if self.do_output:
                print('SLEEPING')
            self.sleeping = True
            pub.sendMessage('sleep')
            pub.sendMessage("animate", action="sleep")
            pub.sendMessage("animate", action="sit")
            pub.sendMessage("power:exit")
            pub.sendMessage("led:off")

    def motion(self):
        self.last_motion = datetime.datetime.now()

    def face(self, name):
        print('Event received, detected ' + name)

    def behave(self):
        if self.last_behave > datetime.datetime.now() - datetime.timedelta(Personality.BEHAVE_INTERVAL):
            return

        self.last_behave = datetime.datetime.now()

        if self.do_output and self.last_output < datetime.datetime.now() - datetime.timedelta(Personality.OUTPUT_INTERVAL):
            self.last_output = datetime.datetime.now()
            self.output()

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
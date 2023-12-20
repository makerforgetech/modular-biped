from pubsub import pub
from datetime import datetime, timedelta
from random import randint, randrange
from modules.config import Config

class Feel:
    INPUT_TYPE_INTERESTING = 0
    INPUT_TYPE_COMPANY = 1
    INPUT_TYPE_SCARY = 2
    INPUT_TYPE_FUN = 3
    INPUT_TYPE_STARTLING = 4
    INPUT_TYPE_MAX = 5

    RANGE_MAX = 100
    RANGE_MIN = 0

    BEHAVE_INTERVAL = 2
    OUTPUT_INTERVAL = 30

    def __init__(self, state):
        self.happiness = Feel.RANGE_MAX / 2
        self.contentment = Feel.RANGE_MAX / 2
        self.attention = Feel.RANGE_MAX / 2
        self.wakefulness = Feel.RANGE_MAX / 2

        self.state = state  # the personality instance
        pub.subscribe(self.loop, 'loop:1')
        pub.subscribe(self.feel, 'loop:10')
        pub.subscribe(self.loop_minute, 'loop:60')
        # pub.subscribe(self.face, 'vision:detect:face') # every loop if a face is detected
        # pub.subscribe(self.motion, 'motion') # every second when detected
        pub.subscribe(self.speech, 'speech') # Speech input detected
        pub.subscribe(self.puppet, 'puppet')  # Being puppeteered

    def loop(self):

        # Throttle face detection behaviour to every second, rather than every loop
        if self.state.behaviours.faces.face_detected:
            self.input(Feel.INPUT_TYPE_INTERESTING)

        # If someone is nearby
        if self.state.behaviours.motion.is_motion():
            self.input(Feel.INPUT_TYPE_COMPANY)

    def feel(self):
        # Get gradually bored and tired
        self.attention = self.limit(self.attention - randint(5,10))
        self.happiness = self.limit(self.happiness - randint(5, 10))
        self.wakefulness = self.limit(self.wakefulness - randint(1, 2))
        self.contentment = self.limit(self.contentment - randint(5, 10))
        # print(f'[Feelings] {str(self.attention)} {str(self.happiness)} {str(self.wakefulness)} {str(self.contentment)}')

    def loop_minute(self):
        # print(f"[Feelings] {str(self.attention)} {str(self.happiness)} {str(self.wakefulness)} {str(self.contentment)}")
        pub.sendMessage('log', msg='[Feeling]' + str(self.get_feelings()))
        pub.sendMessage('led', identifiers='status3', color=self.attention, gradient='bg')
        pub.sendMessage('led', identifiers='status4', color=self.happiness, gradient='bg')

    def get_feelings(self):
        feelings = []
        if self.attention > 90 and self.wakefulness > 90:
            feelings.append('excited')
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

    def input(self, input_type):
        # print('Feeling input: ' + str(input_type))
        if input_type == Feel.INPUT_TYPE_INTERESTING:
            # Should make me more attentive and wake me up a little
            self.attention = Feel.RANGE_MAX
            self.happiness += 10
            self.wakefulness += 10
            self.contentment += 30
        elif input_type == Feel.INPUT_TYPE_COMPANY:
            # Has to keep me awake a little, otherwise nothing wakes me up again!
            self.happiness += 10
            self.wakefulness += 5
            self.contentment += 10
        elif input_type == Feel.INPUT_TYPE_SCARY:
            # Should make me more attentive, but less content and happy
            self.attention = Feel.RANGE_MAX
            self.happiness -= 20
            self.wakefulness += 50
            self.contentment -= 30
        elif input_type == Feel.INPUT_TYPE_FUN:
            # Should make me much happer and attentive, wake me up and make me feel more content
            self.attention += 50
            self.happiness += 50
            self.wakefulness += 50
            self.contentment += 50
        elif input_type == Feel.INPUT_TYPE_STARTLING:
            # Should make me more attentive and awake, but less content and happy
            self.attention = Feel.RANGE_MAX
            self.happiness -= 40
            self.wakefulness = Feel.RANGE_MAX
            self.contentment -= 10
        elif input_type == Feel.INPUT_TYPE_MAX:
            # Should make me more attentive and awake, but less content and happy
            self.attention = Feel.RANGE_MAX
            self.happiness =  Feel.RANGE_MAX
            self.wakefulness = Feel.RANGE_MAX
            self.contentment =  Feel.RANGE_MAX
        # print(str(self.attention) + ' ' + str(self.happiness) + ' ' + str(self.wakefulness) + ' ' + str(self.contentment))

    @staticmethod
    def limit(val):
        if val > Feel.RANGE_MAX:
            val = Feel.RANGE_MAX
        elif val < Feel.RANGE_MIN:
            val = Feel.RANGE_MIN
        return val

    def speech(self, msg):
        # It's fun to talk to someone
        self.input(Feel.INPUT_TYPE_FUN)

    def puppet(self):
        self.input(Feel.INPUT_TYPE_MAX)

    # def motion(self):
    #     self.input(Feel.INPUT_TYPE_COMPANY)
    #
    # def face(self, name):
    #     self.input(Feel.INPUT_TYPE_INTERESTING)
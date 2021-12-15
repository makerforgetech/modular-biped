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

    BEHAVE_INTERVAL = 2
    OUTPUT_INTERVAL = 30

    def __init__(self, state):
        # percentages
        self.happiness = 50
        self.contentment = 50
        self.attention = 50
        self.wakefulness = 50

        self.state = state  # the personality instance
        pub.subscribe(self.loop, 'loop:1')
        pub.subscribe(self.loop_minute, 'loop:60')
        pub.subscribe(self.face, 'vision:detect:face')
        pub.subscribe(self.motion, 'motion')

        # pub.sendMessage('led', identifiers=['right','left'], color='blue') # right
        # pub.sendMessage('led', identifiers='left', color='red') # left

    def loop(self):
        self.attention = self.limit(self.attention - randint(5,10))
        self.happiness = self.limit(self.happiness - randint(5, 10))
        self.wakefulness = self.limit(self.wakefulness - randint(1, 2))
        self.contentment = self.limit(self.contentment - randint(5, 10))

        pub.sendMessage('led', identifiers='top_right', color=self.wakefulness) # top right
        pub.sendMessage('led', identifiers='top_left', color=self.attention) # top left
        pub.sendMessage('led', identifiers='bottom_left', color=self.happiness) # bottom left
        pub.sendMessage('led', identifiers='bottom_right', color=self.contentment) # bottom right

    def loop_minute(self):
        # print(f"[Feelings] {str(self.attention)} {str(self.happiness)} {str(self.wakefulness)} {str(self.contentment)}")
        pub.sendMessage('log', msg='[Feeling]' + str(self.get_feelings()))

    def get_feelings(self):
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

    def input(self, input_type):
        # print('Feeling input: ' + str(input_type))
        if input_type == Feel.INPUT_TYPE_INTERESTING:
            self.attention = 100
            self.happiness += 10
            self.wakefulness += 10
            self.contentment += 30
        elif input_type == Feel.INPUT_TYPE_COMPANY:
            self.happiness += 10
            self.contentment += 10
        elif input_type == Feel.INPUT_TYPE_SCARY:
            self.attention = 100
            self.happiness = 20
            self.wakefulness += 50
            self.contentment -= 30
        elif input_type == Feel.INPUT_TYPE_FUN:
            self.attention = 100
            self.happiness = 100
            self.wakefulness += 50
            self.contentment += 50
        elif input_type == Feel.INPUT_TYPE_STARTLING:
            self.attention = 100
            self.happiness -= 40
            self.wakefulness += 50
            self.contentment -= 10
        # print(str(self.attention) + ' ' + str(self.happiness) + ' ' + str(self.wakefulness) + ' ' + str(self.contentment))

    @staticmethod
    def limit(val):
        if val > 100:
            val = 100
        elif val < 0:
            val = 0
        return val

    def motion(self):
        self.input(Feel.INPUT_TYPE_COMPANY)

    def face(self, name):
        self.input(Feel.INPUT_TYPE_INTERESTING)
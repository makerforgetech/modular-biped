from pubsub import pub

class Feel:
    INPUT_TYPE_INTERESTING = 0
    INPUT_TYPE_SCARY = 1
    INPUT_TYPE_FUN = 1
    INPUT_TYPE_STARTLING = 1

    BEHAVE_INTERVAL = 2
    OUTPUT_INTERVAL = 30

    def __init__(self, state):
        self.happiness = 50
        self.contentment = 50
        self.attention = 50
        self.wakefulness = 100

        self.state = state  # the personality instance
        self.last_behave = datetime.now()
        pub.subscribe(self.input, 'behaviour')
        pub.subscribe(self.loop, 'loop:60')

    def loop(self):
        self.attention += randint(-20, 20)
        self.happiness += randint(-2, 2)
        self.wakefulness -= randint(0, 3)
        self.contentment -= randint(0, 3)

    def behave(self):
        if self.last_behave > self.past(Personality.BEHAVE_INTERVAL):
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
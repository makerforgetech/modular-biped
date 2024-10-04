from random import randint, randrange
from pubsub import pub
from datetime import datetime, timedelta

from modules.config import Config

class Objects:
    def __init__(self, state):
        self.state = state # the personality instance
        self.last_detection = None
        self.is_detected = None
        pub.subscribe(self.object, 'vision:detect:object')
        pub.subscribe(self.noobject, 'vision:nomatch')

    def noobject(self):
        if self.is_detected:
            pub.sendMessage('log:info', msg='[Personality] No object matches found')
            self.is_detected = False

    def object(self, name):
        if not self.is_detected:
            pub.sendMessage('log:info', msg='[Personality] Object detected: ' + name)
        self.is_detected = True
        self.last_detection = datetime.now()
        # self.state.set_state(Config.STATE_IDLE)
        self.state.set_eye('purple')

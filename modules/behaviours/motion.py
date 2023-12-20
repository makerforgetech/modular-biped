from random import randint, randrange
from pubsub import pub
from datetime import datetime, timedelta

from modules.config import Config

class Motion:
    def __init__(self, state):
        self.state = state # the personality instance
        self.last_motion = datetime.now()
        pub.subscribe(self.motion, 'motion')

    def motion(self):
        self.last_motion = datetime.now()
        # print(self.last_motion)
        if not self.state.behaviours.faces.face_detected and self.state.lt(self.state.behaviours.faces.last_face, self.state.past(2)):
            self.state.set_eye('blue')
            pub.sendMessage('vision:start')

    def is_motion(self):
        return not self.state.lt(self.state.behaviours.motion.last_motion, self.state.past(2))
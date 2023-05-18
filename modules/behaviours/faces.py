from random import randint, randrange
from pubsub import pub
from datetime import datetime, timedelta

from modules.config import Config

class Faces:
    def __init__(self, state):
        self.state = state # the personality instance
        self.last_face = None
        self.last_face_name = None
        self.current_faces = []
        self.face_detected = None
        pub.subscribe(self.face, 'vision:detect:face')
        pub.subscribe(self.noface, 'vision:nomatch')

    def noface(self):
        pub.sendMessage('log:info', msg='[Personality] No face matches found')
        self.face_detected = False

    def face(self, name):
        pub.sendMessage('log:info', msg='[Personality] Face detected: ' + str(name))
        self.face_detected = True
        self.last_face = datetime.now()
        # self.state.set_state(Config.STATE_IDLE)
        if name == 'Unknown':
            self.state.set_eye('purple')
        else:
            # self.set_state(Config.STATE_ALERT)  # This overrides the tracking so we can't trigger this here
            self.state.set_eye('green')
            if name not in self.current_faces:
                self.current_faces.append(name)
                pub.sendMessage('speak', message=name)

        if name != 'Unknown':
            self.last_face_name = name
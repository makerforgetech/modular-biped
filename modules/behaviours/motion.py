from random import randint, randrange
from pubsub import pub

class Motion:
    def __init__(self, state):
        self.state = state # the personality instance
        self.last_motion = datetime.now()
        pub.subscribe(self.motion, 'motion')

    def motion(self):
        self.last_motion = datetime.now()
        if not self.state.faces.face_detected and self.state.lt(self.state.faces.last_face, self.state.past(2)):
            self.state.set_eye('blue')
from pubsub import pub
from modules.config import Config

class Dream:
    def __init__(self, state):
        self.state = state  # the personality instance
        pub.subscribe(self.behave_nightly, 'loop:nightly')

    def behave_nightly(self):
        # This will attempt to process anything in the 'matches/verified' directory, or return if nothing to process
        if self.state.is_asleep() and Config.is_night():
            pub.sendMessage('log', msg="[Personality] Training model")
            pub.sendMessage('vision:train')
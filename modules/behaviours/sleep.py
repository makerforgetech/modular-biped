from pubsub import pub
from time import sleep, localtime
from modules.config import Config
class Sleep:
    SLEEP_TIMEOUT = 2 * 60
    REST_TIMEOUT = 2 * 60

    def __init__(self, state):
        self.state = state  # the personality instance
        pub.subscribe(self.loop, 'loop:1')

    def loop(self):
        if self.state.is_asleep():
            sleep(5)

        # if sleeping and not tired, then wake (during the day)
        if self.state.is_asleep() and not Config.is_night() and 'tired' not in self.state.behaviours.feel.get_feelings():
            self.state.set_state(Config.STATE_RESTING)

        # if not sleeping tired, sleep
        elif not self.state.is_asleep() and 'tired' in self.state.behaviours.feel.get_feelings():
            self.state.set_state(Config.STATE_SLEEPING)

        # if not resting and bored, rest
        elif not self.state.is_resting() and 'bored' in self.state.behaviours.feel.get_feelings():
            self.state.set_state(Config.STATE_RESTING)

        elif 'ok' in self.state.behaviours.feel.get_feelings():
            self.state.set_state(Config.STATE_IDLE)

        elif 'excited' in self.state.behaviours.feel.get_feelings():
            self.state.set_state(Config.STATE_ALERT)
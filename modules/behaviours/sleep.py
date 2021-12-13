from pubsub import pub

class Sleep:
    SLEEP_TIMEOUT = 2 * 60
    REST_TIMEOUT = 30

    def __init__(self, state):
        self.state = state  # the personality instance
        pub.subscribe(self.loop, 'loop:1')

    def loop(self):
        if self.state.is_asleep():
            sleep(5)

        # if sleeping and motion detected in the last X seconds, then wake (during the day)
        if self.state.is_asleep() and not Personality.is_night() and self.state.behaviours.motion.last_motion > self.state.past(10):
            self.state.set_state(Personality.STATE_RESTING)

        # if not sleeping and motion not detected for SLEEP_TIMEOUT, sleep
        if not self.state.is_asleep() and self.state.lt(self.state.behaviours.motion.last_motion, self.state.past(Sleep.SLEEP_TIMEOUT)):
            self.state.set_state(Personality.STATE_SLEEPING)

        # if not resting and faces not detected for REST_TIMEOUT, rest
        if not self.state.is_resting() and self.state.lt(self.state.behaviours.faces.last_face, self.state.past(Sleep.REST_TIMEOUT)):
            self.state.set_state(Personality.STATE_RESTING)
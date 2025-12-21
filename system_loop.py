
import time
import yaml
import os

class SystemLoop:
    STATE_STOPPED = 0
    STATE_SLEEPING = 1
    STATE_THROTTLED = 2
    STATE_RUNNING = 3
    DEFAULT_SLEEP_INTERVAL = 0.01  # 10ms
    
    def __init__(self, messaging_service):
        self.messaging_service = messaging_service
        self._state = SystemLoop.STATE_RUNNING
        self._state_requests = {}
        self._motion_state = self._state # To remember previous state before sleeping due to motion
        self._second_loop = time.time()
        self._ten_second_loop = time.time()
        self._minute_loop = time.time()
        self.sleep_interval = SystemLoop.DEFAULT_SLEEP_INTERVAL
        # Subscribe to system/sleep and system/wake
        self.messaging_service.subscribe('system/sleep', self.log_state_request, state=SystemLoop.STATE_SLEEPING)
        self.messaging_service.subscribe('system/wake', self.log_state_request, state=SystemLoop.STATE_RUNNING)
        self.messaging_service.subscribe('system/throttle', self.log_state_request, state=SystemLoop.STATE_THROTTLED)
        self.messaging_service.subscribe('gpio/motion', self._last_motion_update)

    def log_state_request(self, requestor, state):
        self._state_requests[requestor] = state
        # print(self._state_requests)
        # self.messaging_service.publish('log', message=f"[SystemLoop] State request from {requestor}: {state}, currently in state: {self._state}")
        self._change_to_lowest_requested_state()
    
    def _change_to_lowest_requested_state(self):
        if not self._state_requests:
            return
        lowest_state = min(self._state_requests.values())
        if lowest_state != self._state:
            self.messaging_service.publish('log', message=f"[SystemLoop] Changing state from {self._state} to {lowest_state} based on requests: {self._state_requests}")
            if lowest_state == SystemLoop.STATE_SLEEPING:
                self._on_sleep()
            elif lowest_state == SystemLoop.STATE_THROTTLED:
                self._on_throttle()
            elif lowest_state == SystemLoop.STATE_RUNNING:
                self._on_wake()

    # Sleep or wake (or throttled) based on seconds since last motion
    # No motion module running = no motion updates, so system stays awake
    def _last_motion_update(self, value):
        self.log_state_request('gpio/motion', SystemLoop.STATE_RUNNING if value is None or value < 30 else SystemLoop.STATE_SLEEPING)
        
    def _on_throttle(self, *args, **kwargs):
        if self._state != SystemLoop.STATE_THROTTLED:
            self._state = SystemLoop.STATE_THROTTLED
            self.sleep_interval = 1  # Increase sleep interval to reduce CPU usage
            self.messaging_service.publish('log', message="[SystemLoop] Received system/throttle. Throttling main loop.")
        
    def _on_sleep(self, *args, **kwargs):
        if self._state != SystemLoop.STATE_SLEEPING:
            self._state = SystemLoop.STATE_SLEEPING
            self.messaging_service.publish('log', message="[SystemLoop] Received system/sleep. Entering sleep mode.")

    def _on_wake(self, *args, **kwargs):
        if self._state != SystemLoop.STATE_RUNNING:
            self._state = SystemLoop.STATE_RUNNING
            self.sleep_interval = SystemLoop.DEFAULT_SLEEP_INTERVAL
            self.messaging_service.publish('log', message="[SystemLoop] Received system/wake. Exiting sleep mode.")

    def start(self):
        self._running = True
        self.messaging_service.publish('log', message=f"[SystemLoop] Loop started using {self.messaging_service.protocol} protocol")
        try:
            self.run()
        except Exception as ex:
            print(ex)
            self.messaging_service.publish('log', message="[SystemLoop] Exception occurred: " + str(ex))
            import traceback
            traceback.print_exc()
        finally:
            self.messaging_service.publish('system/exit')
            self.messaging_service.publish('log', message="[SystemLoop] Loop ended")

    def stop(self):
        self._running = False

    def run(self):
        while self._state != SystemLoop.STATE_STOPPED:
            if self.sleep_interval > 0: 
                time.sleep(self.sleep_interval)
            if self._state == SystemLoop.STATE_SLEEPING:
                continue
            self.messaging_service.publish('system/loop') # @todo consider the best approach to handling sleep mode.
            now = time.time()
            if now - self._second_loop > 1:
                self._second_loop = now
                self.messaging_service.publish('system/loop/1')
            if now - self._ten_second_loop > 10:
                self._ten_second_loop = now
                self.messaging_service.publish('system/loop/10')
            if now - self._minute_loop > 60:
                self._minute_loop = now
                self.messaging_service.publish('system/loop/60')
                self.messaging_service.publish('log', message=f"System currently in state: {self._state} with sleep interval: {self.sleep_interval}s")
            

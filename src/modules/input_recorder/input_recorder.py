import os
import json
import time
from modules.base_module import BaseModule

class InputRecorder(BaseModule):
    def __init__(self, **kwargs):
        super().__init__()
        self.recording = False
        self.events = []
        self.animations_dir = kwargs.get('animations_dir', os.path.join(os.path.dirname(os.path.realpath(__file__)), '../animations'))
        os.makedirs(self.animations_dir, exist_ok=True)
        self.filename = None

    def setup_messaging(self):
        self.subscribe('record/start', self.start_recording )
        self.subscribe('record/stop', self.stop_recording )
        self.subscribe('controller/event', self.handle_event)

    def start_recording(self):
        self.toggle_recording(enable=True)
        
    def stop_recording(self):
        self.toggle_recording(enable=False)
        
    def toggle_recording(self, enable=True, filename=None):
        if enable and not self.recording:
            self.recording = True
            self.events = []
            self.filename = filename or f"recording_{int(time.time())}.json"
            self.log(f"Recording started: {self.filename}")
        elif not enable and self.recording:
            self.recording = False
            self.save_events()
            self.log(f"Recording stopped and saved: {self.filename}")

    def handle_event(self, event):
        if self.recording:
            event['timestamp'] = time.time()
            self.events.append(event)
            self.log(f"Event recorded: {event}")

    def save_events(self):
        if not self.events or not self.filename:
            return
        path = os.path.join(self.animations_dir, self.filename)
        with open(path, 'w') as f:
            json.dump(self.events, f, indent=2)
        self.events = []
        self.filename = None

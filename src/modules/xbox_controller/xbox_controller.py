import threading
import time
import struct
from modules.base_module import BaseModule

"""
Xbox Controller Module

This module provides an interface to control and read input from an Xbox One controller.
"""

class XboxController(BaseModule):
    """
    Module for handling Xbox One controller input.
    """
    JS_EVENT_BUTTON = 0x01
    JS_EVENT_AXIS = 0x02
    JS_EVENT_INIT = 0x80
    JS_EVENT_FORMAT = "IhBB"
    JS_EVENT_SIZE = struct.calcsize(JS_EVENT_FORMAT)
    CONNECT_TIMEOUT = 30  # Seconds to wait for device connection before stopping

    def __init__(self, **kwargs):
        self.running = False
        self.mapping = kwargs.get('mapping', {}) # Must pass this in from consumer
        self.global_deadzone = kwargs.get('deadzone', 0.0)
        self.device = kwargs.get('device', "/dev/input/js0") # Required to specify the gamepad device
        if 'button_names' not in kwargs:
            raise ValueError("button_names must be provided in configuration")
        if 'axis_names' not in kwargs:
            raise ValueError("axis_names must be provided in configuration")
        self.button_names = kwargs['button_names']
        self.axis_names = kwargs['axis_names']
        self.axis_range = (kwargs.get('axis_min', -32767.0), kwargs.get('axis_max', 32767.0))
        self.debug = kwargs.get('debug', False)
        self.start = kwargs.get('start', 0) # For most axis inputs the start pos will be 0, but for some it fully negative. This accommodates that in the deadzone.
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.current_status = {}
        self.current_status_normalized = {}
        self.normalized = kwargs.get('normalised', True)
        self._previous_status = {}

        
    def setup_messaging(self):
        self.running = True
        self.thread.start()

    def _listen(self):
        """Poll the joystick device for input events."""
        self.log("Controller listening for input...")
        error = None
        while self.running:
            try:
                with open(self.device, "rb") as jsdev:
                    if error is not None:
                        self.log(f"Gamepad connected at {self.device}", level='info')
                        error = None
                    while self.running:
                        evbuf = jsdev.read(self.JS_EVENT_SIZE)
                        if not evbuf:
                            continue
                        time_ms, value, type_, number = struct.unpack(self.JS_EVENT_FORMAT, evbuf)
                        if self.normalized:
                            # Normalized data
                            self._handle_event(time_ms, type_, value, number)
                            if self.debug:
                                self.output_normalized_status()
                        else:
                            # Raw data
                            self.current_status[(type_, number)] = evbuf
                            if self.debug:
                                self.output_current_status()
                        
                        
                        
            except FileNotFoundError:
                if error is None:
                    self.log(f"No gamepad found at {self.device}. Waiting {self.CONNECT_TIMEOUT} seconds for connection...", level='warning')
                    error = time.time()
                elif (time.time() - error) > self.CONNECT_TIMEOUT:
                    self.log(f"No gamepad found at {self.device}. Stopping controller module", level='warning')
                    self.running = False
                time.sleep(1)
                
    def get_current_status(self, normalized=True):
        if normalized:
            return self.current_status_normalized
        return self.current_status
                
    def _get_name(self, type_, number):
        # Get the name of a button or axis based on its type and number
        if type_ == self.JS_EVENT_BUTTON:
            return self.button_names.get(number, f"button_{number}")
        elif type_ == self.JS_EVENT_AXIS:
            return self.axis_names.get(number, f"axis_{number}")
        return f"unknown_{number}"
    
    def _get_mapping(self, name):
        return self.mapping.get(name, None)
    
    def _handle_event(self, time_ms, type_, value, number):
        if type_ == self.JS_EVENT_BUTTON:
            self._handle_button_event(time_ms, type_, value, number)
        elif type_ == self.JS_EVENT_AXIS:
            self._handle_axis_event(time_ms, type_, value, number)
    
    def _handle_button_event(self, time_ms, type_, value, number):
        button_name = self._get_name(type_, number)
        # Normalise to 0.0 or 1.0
        norm_value = 1.0 if value else 0.0
        self.current_status_normalized[button_name] = norm_value
    
    def _handle_axis_event(self, time_ms, type_, value, number):
        button_name = self._get_name(type_, number)
        mapping = self._get_mapping(button_name)
        start = mapping.start if mapping else 0
        # dz = mapping.deadzone if mapping else self.global_deadzone
        # if abs(value - start) < dz:
            # return  # Within deadzone
        # Normalise to -1.0 to 1.0
        norm_value = 0.0
        min_axis, max_axis = self.axis_range
        norm_value = (value - start) / (max_axis - start) if value >= start else (value - start) / (start - min_axis)    
        self.current_status_normalized[button_name] = round(norm_value,3)
        
    def get_changed_inputs(self):
        """Return a list of inputs from the controller that have changed since the last check."""
        status = self.get_current_status(normalized=self.normalized).copy() # Copy to avoid changes during iteration
        changed_inputs = []
        for name, value in status.items():
            if self._has_input_changed(name, value, self._previous_status):
                changed_inputs.append((name, value))
        self._previous_status = {name: value for name, value in status.items()}
        return changed_inputs
    
    def _has_input_changed(self, name, value, previous_status):
        """Check if the input value has changed since the last check."""
        previous_value = previous_status.get(name, None)
        return previous_value != value
        

    def output_current_status(self):
        # output a single line list of all current_status values, mapped to button/axis names
        line = []
        for type_, evbuf in self.current_status.items():
            time_ms, value, type_, number = struct.unpack(self.JS_EVENT_FORMAT, evbuf)
            if type_ == self.JS_EVENT_INIT:
                continue
            if (type_ == self.JS_EVENT_BUTTON and number in self.button_names) or (type_ == self.JS_EVENT_AXIS and number in self.axis_names):
                # Format value to fixed width 7 (including minus sign)
                value_str = f"{value:7d}"
                name = self.button_names[number] if type_ == self.JS_EVENT_BUTTON else self.axis_names[number]
                line.append(f"{name}:{value_str}")
        print(" | ".join(line), end='\r', flush=True)
        
    
    def output_normalized_status(self):
        # output a single line list of all current_status_normalized values, mapped to button/axis names
        line = []
        for name, norm_value in self.current_status_normalized.items():
            value_str = f"{norm_value: .3f}"
            line.append(f"{name}:{value_str}")
        print(" | ".join(line), end='\r', flush=True)
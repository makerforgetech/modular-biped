import struct
import threading
import time
import inspect

from modules.base_module import BaseModule


class Controller(BaseModule):
    """Handles gamepad/joystick input and maps events to pub/sub topics."""

    # Joystick event constants
    JS_EVENT_BUTTON = 0x01
    JS_EVENT_AXIS = 0x02
    JS_EVENT_INIT = 0x80
    JS_EVENT_FORMAT = "IhBB"
    JS_EVENT_SIZE = struct.calcsize(JS_EVENT_FORMAT)
    CONNECT_TIMEOUT = 30  # Seconds to wait for device connection before stopping

    def __init__(self, **kwargs):
        self.running = False
        self.button_action_map = kwargs.get('button_action_map', {})
        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.global_deadzone = kwargs.get('deadzone', 0.0)
        self.global_debounce = kwargs.get('debounce', 100)  # Minimum change threshold
        self.modifier_buttons = set(kwargs.get('modifier_buttons', [])) # Allow alternate mappings when these buttons are held
        self.pressed_buttons = set()
        self.axis_last_value = {}  # Track last value for each axis
        self.axis_last_time = {}   # Track last event time (ms) for each axis
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

    def _get_active_mapping(self):
        """Get the current button map based on pressed modifier buttons."""
        active_mods = sorted(self.pressed_buttons & self.modifier_buttons)
        mapping_key = '+'.join(active_mods) if active_mods else 'default'
        return self.button_action_map.get(mapping_key, self.button_action_map.get('default', {}))

    def setup_messaging(self):
        self.running = True
        self.thread.start()

    def listen(self):
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
                        self._handle_js_event(time_ms, value, type_, number)
            except FileNotFoundError:
                if error is None:
                    self.log(f"No gamepad found at {self.device}. Waiting {Controller.CONNECT_TIMEOUT} seconds for connection...", level='warning')
                    error = time.time()
                elif (time.time() - error) > Controller.CONNECT_TIMEOUT:
                    self.log(f"No gamepad found at {self.device}. Stopping controller module", level='warning')
                    self.running = False
                time.sleep(1)

    def _handle_js_event(self, time_ms, value, type_, number):
        """Route joystick events to appropriate handlers."""
        is_init = (type_ & self.JS_EVENT_INIT) != 0
        event_type = type_ & ~self.JS_EVENT_INIT

        topics_args = []
        if event_type == self.JS_EVENT_BUTTON:
            topics_args = self._handle_button_event(value, number, collect_topics_args=True)
        elif event_type == self.JS_EVENT_AXIS:
            topics_args = self._handle_axis_event(value, number, collect_topics_args=True)
        self.publish('controller/event', event={
            'time_ms': time_ms,
            'value': value,
            'type': type_,
            'number': number,
            'topics_args': topics_args
        })

    def _handle_button_event(self, value, number, collect_topics_args=False):
        """Handle button press/release events."""
        button = self.button_names.get(number, f'BTN_{number}')
        topic = None
        args = {}
        topics_args = []

        if value == 1:
            self.pressed_buttons.add(button)
        elif value == 0:
            self.pressed_buttons.discard(button)

        button_map = self._get_active_mapping()
        if button in button_map and value == 1:
            for mapping in button_map[button]:
                topic = mapping.get('topic')
                if not topic:
                    self.log(f"Empty topic for button {button} mapping, skipping.", level='warning')
                    continue
                args = mapping.get('args', {})
                self.publish(topic, **args)
                self.log(f"Published to topic {topic} with args {args} (jsdev)")
                topics_args.append({'topic': topic, 'args': args})

        # If collect_topics_args is set, return the list, else preserve old behavior
        frame = inspect.currentframe().f_back
        if frame and 'collect_topics_args' in frame.f_locals and frame.f_locals['collect_topics_args']:
            return topics_args
        return topic, args
    
    def _debug_axis_events(self):
        axis_states = []
        button_map = self._get_active_mapping()
        for a in sorted(self.axis_last_value.keys()):
            v = self.axis_last_value[a]
            dz_check = self._axis_in_deadzone(button_map, v, a)
            val_str = f"{v:8.0f}"
            # Ensure deadzone is always positive for comparison
            if dz_check:
                val_str = f"[{v:6.0f}]"
            axis_states.append(f"{a}: {val_str}")
        return axis_states
    
    def _axis_in_deadzone(self, button_map, value, axis):
        dz = self.global_deadzone
        start = self.start
        if axis in button_map:
            mapping = button_map[axis][0] if button_map[axis] else {}
            dz = mapping.get('deadzone', self.global_deadzone)
            start = mapping.get('start', self.start)
        return abs(value - start) < dz
            
    def _handle_axis_event(self, value, number, collect_topics_args=False):
        """
        Handle axis movement events with proportional, smooth servo movement.
        In debug mode, prints all current axis values on a single line in realtime.
        """
        axis = self.axis_names.get(number, f'AXIS_{number}')
        topic = None
        args = {}
        topics_args = []
        
        if self.debug:
            # Track the latest value for each axis
            self.axis_last_value[axis] = value
            # Print all current axis values on a single line, bracketing those within deadzone
            axis_states = self._debug_axis_events()
            
            print(" | ".join(axis_states), end='\r', flush=True)
            # In debug mode, do not publish events
            return []

        button_map = self._get_active_mapping()
        if axis not in button_map:
            frame = inspect.currentframe().f_back
            if frame and 'collect_topics_args' in frame.f_locals and frame.f_locals['collect_topics_args']:
                return topics_args
            return topic, args

        # Axis normalization: guess max range from observed values or config
        norm_value = max(min(value, self.axis_range[1]), self.axis_range[0]) / self.axis_range[1]  # Clamp and normalize to [-1, 1]
        # self.log(f"Axis {axis} raw value: {value}, normalized: {norm_value}")

        now = int(time.monotonic() * 1000)
        last_time = self.axis_last_time.get(axis)

        for mapping in button_map[axis]:
            
            ## Check debuounce time
            if last_time is not None:
                debounce = mapping.get('debounce', self.global_debounce)
                if (now - last_time) < debounce:
                    continue
            
            if self._axis_in_deadzone(button_map, value, axis):
                continue
            
            topic = mapping.get('topic')
            if not topic:
                self.log(f"Empty topic for axis {axis} mapping, skipping.", level='warning')
                continue

            args = dict(mapping.get('args', {}))
            args['delta'] = self._axis_val_to_delta(norm_value, mapping)
            if args['delta'] != 0:
                self.log(f"Publishing to topic {topic} with args {args} (jsdev)")
                self.publish(topic, **args)
                topics_args.append({'topic': topic, 'args': args})

        if topics_args:
            self.axis_last_time[axis] = now

        frame = inspect.currentframe().f_back
        if frame and 'collect_topics_args' in frame.f_locals and frame.f_locals['collect_topics_args']:
            return topics_args
        return topic, args
    
    def _axis_val_to_delta(self, value, mapping):
        """Convert raw axis value to delta based on mapping configuration."""
        modifier = mapping.get('modifier')
        scale = 1.0
        if modifier is not None:
            scale = modifier.get('scale', 1.0)

        max_delta = mapping.get('max_delta', 50)
        delta = int(value * scale * max_delta)
        return delta

    # Keep public method for backwards compatibility with tests
    def handle_js_event(self, time_ms, value, type_, number):
        """Public wrapper for _handle_js_event (for testing compatibility)."""
        return self._handle_js_event(time_ms, value, type_, number)

    def stop(self):
        """Stop the controller listener thread."""
        self.running = False
        self.thread.join()
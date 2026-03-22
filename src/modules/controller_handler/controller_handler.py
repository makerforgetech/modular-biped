import time
from modules.base_module import BaseModule

class ControllerHandler(BaseModule):
    """
    Consume controller input and map to messaging events.

    Requires injection of a controller module that provides input data.
    """
    def __init__(self, **kwargs):
        self.controller = None
        self.mapping = kwargs.get('mapping', {})
        self.modifier_buttons = kwargs.get('modifier_buttons', [])
        self.debug = kwargs.get('debug', False)
        self.debounce_time = kwargs.get('debounce_time', 0.5)  # seconds
        self.running = False
        self._last_action_time = {}
    
    def start(self):
        self.running = True
        self.log("Controller Handler started", level='info')

    def loop(self):
        """Called every system loop cycle to process controller input."""
        if self.running:
            self._process_input()
        
    def _process_input(self):
        """Process input from the controller and publish corresponding events."""
        if not self.controller:
            self.log("No controller module injected", level='warning')
            return
        
        status = self.controller.get_current_status(normalized=True)
        active_modifiers = [btn for btn in self.modifier_buttons if status.get(btn, 0) > 0.5]
        active_modifier_key = '+'.join(sorted(active_modifiers)) if active_modifiers else 'default'
        
        # Get mapping for current modifier state
        current_mapping = self.mapping.get(active_modifier_key, {})
        
        inputs = self.controller.get_changed_inputs()
        
        if inputs and self.debug:
            print(inputs)
        
        for name, value in inputs:
            if self._last_action_time.get(name, None) and time.time() - self._last_action_time.get(name) < self.debounce_time :
                continue
            mapping = self._get_mapping(name, current_mapping)
            if mapping is None:
                continue
            for action in mapping.get('actions', []):
                topic = action.get('topic')
                if not topic:
                    continue
                args = action.get('args', {}).copy()
                # Modify scale of value and pass as delta
                if action.get('modifier', {}).get('scale', None) is not None:
                    args['delta'] = value * action.get('modifier', {}).get('scale', 1)
                # Map value to scaled range and pass as delta
                elif action.get('modifier', {}).get('mapping', None) is not None:
                    min, max = action.get('modifier', {}).get('mapping', None)
                    args['delta'] = min + (value + 1) * (max - min) / 2
                if self.debug:
                    self.log(f"Publishing {topic} with args {args} for input {name} on modifier: {active_modifier_key}")
                self.publish(topic, **args)
                self._last_action_time[name] = time.time()
    
    def _get_mapping(self, input_name, mapping):
        """Get the mapping for a specific button."""
        return mapping.get(input_name, None)
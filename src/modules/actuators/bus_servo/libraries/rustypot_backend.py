from .bus_servo_base import BusServoBase
from .utils import degrees_to_radians, radians_to_degrees
import numpy as np

class RustypotBusServo(BusServoBase):
    # Class-level dictionary to store controller singletons by (port, baudrate)
    _controller_singletons = {}

    def __init__(self, servo_id, model, port, baudrate=1000000, range=None, range_degrees=None, **kwargs):
        super().__init__(servo_id, model, port, baudrate, range, **kwargs)
        key = (port)
        if key in RustypotBusServo._controller_singletons:
            self.controller = RustypotBusServo._controller_singletons[key]['controller']
            # Set max_rad/min_rad based on the controller type already created
            self.max_rad = RustypotBusServo._controller_singletons[key]['max_rad']
            self.min_rad = RustypotBusServo._controller_singletons[key]['min_rad']
            existing_model = RustypotBusServo._controller_singletons[key]['model']
            if (model.startswith('ST') and not existing_model.startswith('ST')) or (model.startswith('SC') and not existing_model.startswith('SC')):
                self.log(f"Warning: Attempted to create a {model} controller for port {port}, but a {existing_model} controller already exists. Reusing the existing controller.")
        else:
            if model.startswith('ST'):
                from rustypot import Sts3215PyController
                controller = Sts3215PyController(port, baudrate, 0.1)
                max_rad = np.deg2rad(360)
                min_rad = 0
            elif model.startswith('SC'):
                from rustypot import Scs0009PyController
                controller = Scs0009PyController(port, baudrate, 0.1)
                max_rad = np.deg2rad(300)
                min_rad = 0
            else:
                raise ValueError(f"Unknown model: {model}")
            RustypotBusServo._controller_singletons[key] = {
                'controller': controller,
                'model': model,
                'max_rad': max_rad,
                'min_rad': min_rad
            }
            self.controller = controller
            self.max_rad = max_rad
            self.min_rad = min_rad
        
    def get_speed(self, unit='degrees'):
        rad_s = self.controller.read_present_speed(self.servo_id)
        if unit == 'degrees':
            import numpy as np
            return np.rad2deg(rad_s)
        elif unit == 'radians':
            return rad_s
        elif unit == 'raw':
            return rad_s  # Not directly supported
        else:
            raise ValueError(f"Unknown unit: {unit}")

    def get_moving(self):
        # Rustypot does not provide a direct moving status; infer from speed
        return self.get_speed(unit='radians') != 0

    def enable_continuous(self):
        # Not supported in rustypot for these servos
        raise NotImplementedError("Continuous mode not supported in rustypot backend.")

    def turn_wheel(self, speed):
        # Not supported in rustypot for these servos
        raise NotImplementedError("Wheel mode not supported in rustypot backend.")

    def handle_errors(self, comm_result, error):
        # Rustypot raises exceptions on error, so just return False for compatibility
        return False

    def calibrate_to_center(self):
        # Move to the center of the configured range
        if self.range:
            center = (self.range[0] + self.range[1]) / 2
            self.move_to(center, unit='degrees')
        else:
            raise ValueError("Range not set for this servo.")

    def move_to(self, value, unit='degrees'):
        if unit == 'degrees':
            rad = np.deg2rad(value)
        elif unit == 'radians':
            rad = value
        elif unit == 'raw':
            # For rustypot, raw is not directly supported; treat as radians in range
            rad = value
        else:
            raise ValueError(f"Unknown unit: {unit}")
        self.controller.write_goal_position(self.servo_id, rad)

    def get_position(self, unit='degrees'):
        rad = self.controller.read_present_position(self.servo_id)
        # Ensure rad is a scalar, not a numpy array
        if isinstance(rad, np.ndarray):
            rad = float(rad.item())
        if unit == 'degrees':
            deg = np.rad2deg(rad)
            if isinstance(deg, np.ndarray):
                deg = float(deg.item())
            return deg
        elif unit == 'radians':
            return float(rad)
        elif unit == 'raw':
            # Not directly supported; return radians as raw
            return float(rad)
        else:
            raise ValueError(f"Unknown unit: {unit}")

    def set_speed(self, value, unit='degrees'):
        # Implement as needed, similar to move_to
        pass

    def detach(self):
        self.controller.write_torque_enable(self.servo_id, False)

    def attach(self):
        self.controller.write_torque_enable(self.servo_id, True)

    def exit(self):
        self.detach()

    def move_to_raw(self, raw_value):
        # Not directly supported; treat as radians
        self.controller.write_goal_position(self.servo_id, raw_value)

    def get_position_raw(self):
        # Not directly supported; return radians
        return self.controller.read_present_position(self.servo_id)

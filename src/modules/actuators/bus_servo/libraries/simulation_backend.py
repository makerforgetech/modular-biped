from .bus_servo_base import BusServoBase
import time

class SimulationBusServo(BusServoBase):
    def __init__(self, servo_id, model, port, baudrate=1000000, range=None, range_degrees=None, **kwargs):
        super().__init__(servo_id, model, port, baudrate, range, range_degrees, **kwargs)
        self.position = (range[0] + range[1]) / 2 if range else 0
        self.speed = 0
        self.torque_enabled = True
        self.is_moving = False
        self.log = kwargs.get('log', print)  # Use BaseModule.log if provided, else print

    def move_to(self, value, unit='degrees'):
        self.log(f"[SIM] Moving servo {self.servo_id} to {value} {unit}")
        self.position = value
        self.is_moving = True
        time.sleep(0.01)
        self.is_moving = False

    def get_position(self, unit='degrees'):
        self.log(f"[SIM] Getting position of servo {self.servo_id} in {unit}")
        return self.position

    def set_speed(self, value, unit='degrees'):
        self.log(f"[SIM] Setting speed of servo {self.servo_id} to {value} {unit}")
        self.speed = value

    def detach(self):
        self.log(f"[SIM] Detaching (disabling torque) servo {self.servo_id}")
        self.torque_enabled = False

    def attach(self):
        self.log(f"[SIM] Attaching (enabling torque) servo {self.servo_id}")
        self.torque_enabled = True

    def exit(self):
        self.log(f"[SIM] Exiting simulation for servo {self.servo_id}")

    def move_to_raw(self, raw_value):
        self.log(f"[SIM] Moving servo {self.servo_id} to raw value {raw_value}")
        self.position = raw_value
        self.is_moving = True
        time.sleep(0.01)
        self.is_moving = False

    def get_position_raw(self):
        self.log(f"[SIM] Getting raw position of servo {self.servo_id}")
        return self.position

    def get_speed(self, unit='degrees'):
        self.log(f"[SIM] Getting speed of servo {self.servo_id} in {unit}")
        return self.speed

    def get_moving(self):
        self.log(f"[SIM] Checking if servo {self.servo_id} is moving")
        return self.is_moving

    def enable_continuous(self):
        self.log(f"[SIM] Enabling continuous mode for servo {self.servo_id}")

    def turn_wheel(self, speed):
        self.log(f"[SIM] Turning wheel of servo {self.servo_id} at speed {speed}")
        self.speed = speed
        self.is_moving = True
        time.sleep(0.01)
        self.is_moving = False

    def handle_errors(self, comm_result, error):
        self.log(f"[SIM] Handling errors for servo {self.servo_id}: comm_result={comm_result}, error={error}")
        return False

    def calibrate_to_center(self):
        if self.range:
            center = (self.range[0] + self.range[1]) / 2
            self.log(f"[SIM] Calibrating servo {self.servo_id} to center position {center}")
            self.position = center
        else:
            self.log(f"[SIM] No range set for servo {self.servo_id}, cannot calibrate to center.")

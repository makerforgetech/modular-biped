from abc import ABC, abstractmethod

class BusServoBase(ABC):
    def __init__(self, servo_id, model, port, baudrate=1000000, range=None, range_degrees=None, **kwargs):
        self.servo_id = servo_id
        self.model = model  # 'ST' or 'SC'
        self.port = port
        self.baudrate = baudrate
        self.range = range
        self.range_degrees = range_degrees

    @abstractmethod
    def get_speed(self, unit='degrees'):
        """Get the current speed of the servo in the specified unit."""
        pass

    @abstractmethod
    def get_moving(self):
        """Get the current moving status of the servo."""
        pass

    @abstractmethod
    def enable_continuous(self):
        """Set the servo to continuous (wheel) mode if supported."""
        pass

    @abstractmethod
    def turn_wheel(self, speed):
        """Turn the servo in wheel mode at the given speed."""
        pass

    @abstractmethod
    def handle_errors(self, comm_result, error):
        """Handle communication errors."""
        pass

    @abstractmethod
    def calibrate_to_center(self):
        """Move the servo to the center of its range."""
        pass
    
    @abstractmethod
    def move_to(self, value, unit='degrees'):
        """Move servo to position in specified unit ('degrees', 'radians', 'raw')."""
        pass

    @abstractmethod
    def get_position(self, unit='degrees'):
        """Get current position in specified unit."""
        pass

    @abstractmethod
    def set_speed(self, value, unit='degrees'):
        """Set speed in specified unit."""
        pass

    @abstractmethod
    def detach(self):
        """Disable torque."""
        pass

    @abstractmethod
    def attach(self):
        """Enable torque."""
        pass

    @abstractmethod
    def exit(self):
        """Cleanup resources."""
        pass

    @abstractmethod
    def move_to_raw(self, raw_value):
        """Move servo to raw position value."""
        pass

    @abstractmethod
    def get_position_raw(self):
        """Get current position as raw value."""
        pass

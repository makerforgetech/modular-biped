from .bus_servo_base import BusServoBase
from .utils import degrees_to_radians, radians_to_degrees, degrees_to_raw, raw_to_degrees, radians_to_raw, raw_to_radians
import math

# Control table address
ADDR_TORQUE_ENABLE         = 40 # Same address for both ST and SC servos
ADDR_SCS_GOAL_ACC          = 41
ADDR_SCS_GOAL_POSITION     = 42 # Used in SCServo move
ADDR_SCS_GOAL_SPEED        = 46
ADDR_SCS_PRESENT_POSITION  = 56

ST_MAX = 4095
SC_MAX = 1024

class WaveshareBusServo(BusServoBase):
    def __init__(self, servo_id, model, port, baudrate=1000000, range=None, range_degrees=None, **kwargs):
        super().__init__(servo_id, model, port, baudrate, range, **kwargs)
        # Import and initialize the correct SDK based on model
        if model.startswith('ST'):
            from .waveshare.STservo_sdk import PortHandler, sts
            self.portHandler = PortHandler(port)
            self.packetHandler = sts(self.portHandler)
            self.max_raw = 4095
            self.min_raw = 0
            self.max_deg = 360
            self.min_deg = 0
        elif model.startswith('SC'):
            from .waveshare.SCservo_sdk import PacketHandler
            self.portHandler = None  # SC uses PacketHandler only
            self.packetHandler = PacketHandler(1)
            self.max_raw = 1023
            self.min_raw = 0
            self.max_deg = 300
            self.min_deg = 0
        else:
            raise ValueError(f"Unknown model: {model}")
        # Open port and set baudrate if needed
        # ...existing code for port setup...

    def move_to(self, value, unit='degrees'):
        if unit == 'degrees':
            raw = degrees_to_raw(value, self.min_deg, self.max_deg, self.min_raw, self.max_raw)
        elif unit == 'radians':
            raw = radians_to_raw(value, math.radians(self.min_deg), math.radians(self.max_deg), self.min_raw, self.max_raw)
        elif unit == 'raw':
            raw = int(value)
        else:
            raise ValueError(f"Unknown unit: {unit}")
        self.move_to_raw(raw)

    def get_position(self, unit='degrees'):
        raw = self.get_position_raw()
        if unit == 'degrees':
            return raw_to_degrees(raw, self.min_deg, self.max_deg, self.min_raw, self.max_raw)
        elif unit == 'radians':
            return raw_to_radians(raw, math.radians(self.min_deg), math.radians(self.max_deg), self.min_raw, self.max_raw)
        elif unit == 'raw':
            return raw
        else:
            raise ValueError(f"Unknown unit: {unit}")

    def set_speed(self, value, unit='degrees'):
        # Implement as needed, similar to move_to
        pass

    def detach(self):
        # Disable torque
        pass

    def attach(self):
        # Enable torque
        pass

    def exit(self):
        # Cleanup
        pass

    def move_to_raw(self, raw_value):
        # Send move command using SDK
        pass

    def get_position_raw(self):
        # Read position using SDK
        pass

    def get_speed(self):
        """
        Get the current speed of the servo.
        """
        if self.model.startswith('ST'):
            # Read STServo present position
            sts_present_position, sts_present_speed, sts_comm_result, sts_error = self.packetHandler.ReadPosSpeed(self.index)
            if not self.handle_errors(sts_comm_result, sts_error):
                return sts_present_speed
        else:
            return self.sc_get_position_speed('speed')
        
    def get_moving(self):
        """
        Get the current moving status of the servo.
        """
        if self.model.startswith('ST'):
            # Read STServo moving status
            moving, sts_comm_result, sts_error = self.packetHandler.ReadMoving(self.index)
            if not self.handle_errors(sts_comm_result, sts_error):
                return moving
        else:
            # SCServo does not have a direct moving status, so we can infer it by checking if speed is non-zero or if position is changing over time.
            speed = self.get_speed()
            return speed != 0
        
    
    def enable_continuous(self):
        """
        Set the servo mode.
        :param mode: Mode to set (e.g., 'wheel', 'position')
        """
        if self.model.startswith('SC'):
            raise ValueError("Continuous mode is not supported for SCServo models.")
        sts_comm_result, sts_error = self.packetHandler.WheelMode(self.index)
        if not self.handle_errors(sts_comm_result, sts_error):
            self.log(f"Servo {self.name} set to wheel mode")

    def turn_wheel(self, speed):
        if self.model.startswith('SC'):
            raise ValueError("Continuous mode is not supported for SCServo models.")
        sts_comm_result, sts_error = self.packetHandler.WriteSpec(self.index, speed, self.acceleration)
        if not self.handle_errors(sts_comm_result, sts_error):
            self.log(f"Servo {self.name} turned at speed {speed}")


    def handle_errors(self, comm_result, error):
        """
        Handle communication errors.
        :param comm_result: Communication result
        :param error: Error code
        """
        if comm_result != COMM_SUCCESS:
            self.log("%s" % self.packetHandler.getTxRxResult(comm_result), level='error')
            # log stack trace for debugging
            return True
        if error != 0:
            self.log("%s" % self.packetHandler.getRxPacketError(error), level='error')
            return True
        return False
    
    def calibrate_to_center(self):
        """
        Move the servo to the center of its range.
        """
        # Write STServo goal position
        
        if self.model.startswith('ST'):
            self.pos = (self.range[0] + self.range[1]) // 2  # Update current position to center
            sts_comm_result, sts_error = self.packetHandler.WritePosEx(self.index, self.pos, self.speed, self.acceleration)
            if not self.handle_errors(sts_comm_result, sts_error):
                self.log(f"Moved servo {self.identifier} to position {self.pos}")
                
        elif self.model.startswith('SC'):
            self.pos = (self.range[0] + self.range[1]) // 2  # Update current position to center
            self.packetHandler.write1ByteTxRx(self.portHandler, self.index, ADDR_SCS_GOAL_ACC, self.acceleration)
            self.packetHandler.write2ByteTxRx(self.portHandler, self.index, ADDR_SCS_GOAL_SPEED, self.speed)
            self.packetHandler.write2ByteTxRx(self.portHandler, self.index, ADDR_SCS_GOAL_POSITION, self.pos)
            self.log(f"Moved servo {self.identifier} to position {self.pos}")

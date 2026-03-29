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

COMM_SUCCESS = 0  # Communication success (matches value in both ST and SC SDKs)

class WaveshareBusServo(BusServoBase):
    # Class-level cache: one PortHandler + PacketHandler per (port, baudrate, model_type).
    # All servo instances sharing a physical bus reuse the same port handle, so the
    # serial port is opened only once regardless of how many servos are managed.
    _port_singletons = {}  # {(port, baudrate, model_type): {portHandler, packetHandler, ...}}

    def __init__(self, servo_id, model, port, baudrate=1000000, range=None, range_degrees=None, **kwargs):
        super().__init__(servo_id, model, port, baudrate, range, **kwargs)
        self.speed = kwargs.get('speed', 300)
        self.acceleration = kwargs.get('acceleration', 50)

        model_type = 'ST' if model.startswith('ST') else ('SC' if model.startswith('SC') else None)
        if model_type is None:
            raise ValueError(f"Unknown model: {model}")
        key = (port, baudrate, model_type)

        if key in WaveshareBusServo._port_singletons:
            # Reuse the already-open port; just grab the shared handles.
            singleton = WaveshareBusServo._port_singletons[key]
            self.portHandler = singleton['portHandler']
            self.packetHandler = singleton['packetHandler']
            self.max_raw = singleton['max_raw']
            self.min_raw = singleton['min_raw']
            self.max_deg = singleton['max_deg']
            self.min_deg = singleton['min_deg']
            singleton['refcount'] += 1
        else:
            # First servo on this (port, baudrate, model_type) — open the port.
            if model.startswith('ST'):
                from .waveshare.STservo_sdk import PortHandler, sts
                portHandler = PortHandler(port)
                packetHandler = sts(portHandler)
                max_raw, min_raw = 4095, 0
                max_deg, min_deg = 360, 0
            elif model.startswith('SC'):
                from .waveshare.SCservo_sdk import PortHandler, PacketHandler
                portHandler = PortHandler(port)
                packetHandler = PacketHandler(1)
                max_raw, min_raw = 1023, 0
                max_deg, min_deg = 300, 0
            else:
                raise ValueError(f"Unknown model: {model}")

            if not portHandler.openPort():
                raise RuntimeError(f"Failed to open port {port} for servo {servo_id}")
            if not portHandler.setBaudRate(baudrate):
                raise RuntimeError(f"Failed to set baudrate {baudrate} for servo {servo_id}")

            WaveshareBusServo._port_singletons[key] = {
                'portHandler': portHandler,
                'packetHandler': packetHandler,
                'max_raw': max_raw,
                'min_raw': min_raw,
                'max_deg': max_deg,
                'min_deg': min_deg,
                'refcount': 1,
            }
            self.portHandler = portHandler
            self.packetHandler = packetHandler
            self.max_raw = max_raw
            self.min_raw = min_raw
            self.max_deg = max_deg
            self.min_deg = min_deg

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
        self.speed = int(value)

    def set_acceleration(self, value):
        self.acceleration = int(value)

    def detach(self):
        if self.model.startswith('ST'):
            self.packetHandler.write1ByteTxRx(self.servo_id, ADDR_TORQUE_ENABLE, 0)
        else:
            self.packetHandler.write1ByteTxRx(self.portHandler, self.servo_id, ADDR_TORQUE_ENABLE, 0)

    def attach(self):
        if self.model.startswith('ST'):
            self.packetHandler.write1ByteTxRx(self.servo_id, ADDR_TORQUE_ENABLE, 1)
        else:
            self.packetHandler.write1ByteTxRx(self.portHandler, self.servo_id, ADDR_TORQUE_ENABLE, 1)

    def exit(self):
        model_type = 'ST' if self.model.startswith('ST') else 'SC'
        key = (self.port, self.baudrate, model_type)
        singleton = WaveshareBusServo._port_singletons.get(key)
        if singleton:
            singleton['refcount'] -= 1
            if singleton['refcount'] <= 0:
                self.portHandler.closePort()
                del WaveshareBusServo._port_singletons[key]

    def move_to_raw(self, raw_value):
        if self.model.startswith('ST'):
            sts_comm_result, sts_error = self.packetHandler.WritePosEx(self.servo_id, raw_value, self.speed, self.acceleration)
            self.handle_errors(sts_comm_result, sts_error)
        else:
            self.packetHandler.write1ByteTxRx(self.portHandler, self.servo_id, ADDR_SCS_GOAL_ACC, self.acceleration)
            self.packetHandler.write2ByteTxRx(self.portHandler, self.servo_id, ADDR_SCS_GOAL_SPEED, self.speed)
            scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(self.portHandler, self.servo_id, ADDR_SCS_GOAL_POSITION, raw_value)
            self.handle_errors(scs_comm_result, scs_error)

    def get_position_raw(self):
        if self.model.startswith('ST'):
            sts_present_position, sts_comm_result, sts_error = self.packetHandler.ReadPos(self.servo_id)
            if not self.handle_errors(sts_comm_result, sts_error):
                return sts_present_position
        else:
            scs_present_position, scs_comm_result, scs_error = self.packetHandler.read2ByteTxRx(self.portHandler, self.servo_id, ADDR_SCS_PRESENT_POSITION)
            if not self.handle_errors(scs_comm_result, scs_error):
                return scs_present_position
        return None

    def get_speed(self, unit='degrees'):
        """
        Get the current speed of the servo.
        """
        if self.model.startswith('ST'):
            # Read STServo present position
            sts_present_position, sts_present_speed, sts_comm_result, sts_error = self.packetHandler.ReadPosSpeed(self.servo_id)
            if not self.handle_errors(sts_comm_result, sts_error):
                return sts_present_speed
        else:
            scs_data, scs_comm_result, scs_error = self.packetHandler.read4ByteTxRx(self.portHandler, self.servo_id, ADDR_SCS_PRESENT_POSITION)
            if not self.handle_errors(scs_comm_result, scs_error):
                from .waveshare.SCservo_sdk.scservo_def import SCS_HIWORD
                return SCS_HIWORD(scs_data)
        return None
        
    def get_moving(self):
        """
        Get the current moving status of the servo.
        """
        if self.model.startswith('ST'):
            # Read STServo moving status
            moving, sts_comm_result, sts_error = self.packetHandler.ReadMoving(self.servo_id)
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
        sts_comm_result, sts_error = self.packetHandler.WheelMode(self.servo_id)
        if not self.handle_errors(sts_comm_result, sts_error):
            self.log(f"Servo {self.servo_id} set to wheel mode")

    def turn_wheel(self, speed):
        if self.model.startswith('SC'):
            raise ValueError("Continuous mode is not supported for SCServo models.")
        sts_comm_result, sts_error = self.packetHandler.WriteSpec(self.servo_id, speed, self.acceleration)
        if not self.handle_errors(sts_comm_result, sts_error):
            self.log(f"Servo {self.servo_id} turned at speed {speed}")


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
        if not self.range:
            return
        center_deg = (self.range[0] + self.range[1]) / 2
        center_raw = degrees_to_raw(center_deg, self.min_deg, self.max_deg, self.min_raw, self.max_raw)
        self.move_to_raw(center_raw)
        self.log(f"Moved servo {self.servo_id} to center position {center_deg} degrees (raw: {center_raw})")

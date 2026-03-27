from .bus_servo_base import BusServoBase
from .utils import degrees_to_radians, radians_to_degrees, degrees_to_raw, raw_to_degrees, radians_to_raw, raw_to_radians
import math
import threading

# Control table address
ADDR_TORQUE_ENABLE         = 40 # Same address for both ST and SC servos
ADDR_SCS_GOAL_ACC          = 41
ADDR_SCS_GOAL_POSITION     = 42 # Used in SCServo move
ADDR_SCS_GOAL_SPEED        = 46
ADDR_SCS_PRESENT_POSITION  = 56

ST_MAX = 4095
SC_MAX = 1024

COMM_SUCCESS = 0  # Communication success (matches value in both ST and SC SDKs)


class _WaveshareConnectionManager:
    """Shared connection pool for Waveshare servo bus connections.

    Multiple WaveshareBusServo instances on the same serial port, baudrate, and
    protocol share a single PortHandler/packetHandler so that writes to the bus
    are serialized through one connection rather than opening the port multiple
    times.  The underlying port is only closed when the last reference is
    released via release().
    """

    _lock = threading.Lock()
    _connections = {}  # key: (port, baudrate, protocol) -> dict

    @classmethod
    def acquire(cls, port, baudrate, protocol, create_connection):
        """Return the shared (portHandler, packetHandler) for the given bus.

        :param port: Serial port path (e.g. '/dev/ttyAMA0')
        :param baudrate: Baud rate integer
        :param protocol: 'ST' or 'SC' – determines which SDK is in use
        :param create_connection: Zero-arg callable that opens the port and
               returns ``(portHandler, packetHandler)``.  Only invoked when no
               existing connection is found for the key.
        :returns: ``(portHandler, packetHandler)``
        """
        key = (port, baudrate, protocol)
        with cls._lock:
            if key not in cls._connections:
                portHandler, packetHandler = create_connection()
                cls._connections[key] = {
                    'portHandler': portHandler,
                    'packetHandler': packetHandler,
                    'ref_count': 0,
                }
            cls._connections[key]['ref_count'] += 1
            conn = cls._connections[key]
            return conn['portHandler'], conn['packetHandler']

    @classmethod
    def release(cls, port, baudrate, protocol):
        """Decrement the reference count for the given bus connection.

        When the count reaches zero the port is closed and the entry is removed.
        """
        key = (port, baudrate, protocol)
        with cls._lock:
            if key not in cls._connections:
                return
            cls._connections[key]['ref_count'] -= 1
            if cls._connections[key]['ref_count'] <= 0:
                try:
                    cls._connections[key]['portHandler'].closePort()
                except OSError:
                    pass
                del cls._connections[key]

    @classmethod
    def reset(cls):
        """Remove all tracked connections without closing ports.

        Intended for use in tests to reset state between test cases.
        """
        with cls._lock:
            cls._connections.clear()


class WaveshareBusServo(BusServoBase):
    def __init__(self, servo_id, model, port, baudrate=1000000, range=None, range_degrees=None, **kwargs):
        super().__init__(servo_id, model, port, baudrate, range, **kwargs)
        self.speed = kwargs.get('speed', 300)
        self.acceleration = kwargs.get('acceleration', 50)
        # Determine protocol and raw/degree limits from model, then acquire or
        # reuse the shared connection for this (port, baudrate, protocol).
        if model.startswith('ST'):
            from .waveshare.STservo_sdk import PortHandler, sts
            self._protocol = 'ST'
            self.max_raw = 4095
            self.min_raw = 0
            self.max_deg = 360
            self.min_deg = 0
            def _create():
                ph = PortHandler(port)
                if not ph.openPort():
                    raise RuntimeError(f"Failed to open port {port} for servo {servo_id}")
                if not ph.setBaudRate(baudrate):
                    raise RuntimeError(f"Failed to set baudrate {baudrate} for servo {servo_id}")
                return ph, sts(ph)
        elif model.startswith('SC'):
            from .waveshare.SCservo_sdk import PortHandler, PacketHandler
            self._protocol = 'SC'
            self.max_raw = 1023
            self.min_raw = 0
            self.max_deg = 300
            self.min_deg = 0
            def _create():
                ph = PortHandler(port)
                if not ph.openPort():
                    raise RuntimeError(f"Failed to open port {port} for servo {servo_id}")
                if not ph.setBaudRate(baudrate):
                    raise RuntimeError(f"Failed to set baudrate {baudrate} for servo {servo_id}")
                return ph, PacketHandler(1)
        else:
            raise ValueError(f"Unknown model: {model}")

        self.portHandler, self.packetHandler = _WaveshareConnectionManager.acquire(
            port, baudrate, self._protocol, _create
        )

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
        _WaveshareConnectionManager.release(self.port, self.baudrate, self._protocol)

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

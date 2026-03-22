#!/usr/bin/env python

import collections
import sys
import select
import time

# if os.name == 'nt':
#     import msvcrt
#     def getch():
#         return msvcrt.getch().decode()
        
# else:
#     import sys, tty, termios
#     fd = sys.stdin.fileno()
#     old_settings = termios.tcgetattr(fd)
#     def getch():
#         try:
#             tty.setraw(sys.stdin.fileno())
#             ch = sys.stdin.read(1)
#         finally:
#             termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
#         return ch

# sys.path.append("..")
# Uses STServo and SCServo SDK library
from modules.actuators.bus_servo.STservo_sdk import PortHandler, sts, COMM_SUCCESS
from modules.actuators.bus_servo.SCservo_sdk import PacketHandler, SCS_LOWORD, SCS_HIWORD, SCS_TOHOST

from modules.base_module import BaseModule

# Control table address
ADDR_TORQUE_ENABLE         = 40 # Same address for both ST and SC servos
ADDR_SCS_GOAL_ACC          = 41
ADDR_SCS_GOAL_POSITION     = 42 # Used in SCServo move
ADDR_SCS_GOAL_SPEED        = 46
ADDR_SCS_PRESENT_POSITION  = 56

ST_MAX = 4095
SC_MAX = 1024

class Servo(BaseModule):
    def __init__(self, **kwargs):
        """
        Servo class
        """
        self.identifier = kwargs.get('name')
        self.model = kwargs.get('model', 'ST')
        self.index = kwargs.get('id')
        self.range = kwargs.get('range')
        self.range_degrees = kwargs.get('range_degrees', None)  # Optional range in degrees for easier control
        self.start = kwargs.get('start') # Default start position
        self.poses = kwargs.get('poses')  # Dictionary of poses
        self.baudrate = kwargs.get('baudrate', 1000000)
        self.port = kwargs.get('port', '/dev/ttyAMA0') # Change as needed, find with `ls /dev/ttyAMA*`
        self.calibrate_on_boot = kwargs.get('calibrate_on_boot', False) # Loop to show position for manual configuration
        self.demonstrate_on_boot = kwargs.get('demonstrate_on_boot', False) # Move to min and max to demonstrate range
        self.center_on_boot = kwargs.get('center_on_boot', False) # Move to center of range on boot
        self.pos = None
        self.speed = kwargs.get('speed', 300) # 3073
        self.acceleration = kwargs.get('acceleration', 50)
        self._move_queue = collections.deque()
        # After loading YAML:
        poses_list = kwargs.get('poses', [])
        # Convert to dict:
        self.poses = {list(pose.keys())[0]: list(pose.values())[0] for pose in poses_list}

        # Initialize PortHandler instance
        # Set the port path
        # Get methods and members of PortHandlerLinux or PortHandlerWindows
        self.portHandler = PortHandler(self.port)
        
        # if model starts with ST or SC, use the appropriate packet handler
        if self.model.startswith('ST'):
            self.packetHandler = sts(self.portHandler)
        elif self.model.startswith('SC'):
            self.packetHandler = PacketHandler(1) # 1 = protocol_end in examples
        else:
            raise ValueError(f"Unknown servo model: {self.model}. Supported models are ST and SC.")

        # Open port
        if not self.portHandler.openPort():
            raise Exception("Failed to open the port")

        # Set port baudrate
        if not self.portHandler.setBaudRate(self.baudrate):
            raise Exception("Failed to change the baudrate")
        
    def detach(self):
        # Detach servo
        if self.model.startswith('ST'):
            # Disable torque for STServo
            sts_comm_result, sts_error = self.packetHandler.write1ByteTxRx(self.index, ADDR_TORQUE_ENABLE, 0)
            if not self.handle_errors(sts_comm_result, sts_error):
                self.log(f"ST Servo {self.identifier} disabled")
        else:
            # Disable torque for SCServo
            scs_comm_result, scs_error = self.packetHandler.write1ByteTxRx(self.portHandler, self.index, ADDR_TORQUE_ENABLE, 0)
            if not self.handle_errors(scs_comm_result, scs_error):
                self.log(f"SC Servo {self.identifier} disabled")
    
    def exit(self):
        self.detach()
        self.portHandler.closePort()

    def setup_messaging(self):
        self.subscribe('servo:' + self.identifier + ':mvabs', self.move)
        self.subscribe('servo:' + self.identifier + ':mv', self.move_relative)
        self.subscribe('servo:' + self.identifier + ':queue', self.move)
        self.subscribe('system/exit', self.exit)
        self.subscribe('servo/pose', self.move_to_pose)
        
        if self.calibrate_on_boot:
            self.calibrate_dynamic() # Log will show current position repeatedly to help with manual configuration
        
        self.pos = self.get_position()  # Get initial position to avoid jumping from unknown position
        
        if self.center_on_boot:
            self.calibrate_to_center()
        
        if self.demonstrate_on_boot:
            self.log(f"Demonstrating servo {self.identifier} movement, speed={self.speed}, acceleration={self.acceleration}")
            if self.range is not None:
                self.move(self.range[0]) # Move to min range
                self.move((self.range[0] + self.range[1]) // 2) # Move to center
                self.move(self.range[1]) # Move to max range
            else:
                self.log(f"Range not set for servo {self.identifier}, cannot demonstrate movement", level='warning')
        
        # Move to start position
        # if self.get_pose_value('stand') is not None:
            # self.start = self.get_pose_value('stand')
        if self.start is not None:
            self.move(self.start)
        
    def move_to_pose(self, pose_name):
        # print(self.poses)
        pose_value = self.poses.get(pose_name)
        # print(f"{self.identifier} - Pose '{pose_name}' value: {pose_value}")
        my_pose_value = pose_value.get(self.identifier)
        print(f"Moving servo {self.identifier} to pose '{pose_name}' with value {my_pose_value}")
        if my_pose_value is not None:
            self.move(my_pose_value)
        else:
            self.log(f"Pose '{pose_name}' not found for servo {self.identifier}", level='warning')
            
    def _sc_write(self, type, value, verbose=False):
        comm_result, error = self.packetHandler.write2ByteTxRx(self.portHandler, self.index, type, value)
        if hasattr(self.packetHandler, 'getTxRxResult') and verbose:
            self.log(f"[SCServo Result] {self.packetHandler.getTxRxResult(comm_result)}")
        if hasattr(self.packetHandler, 'getRxPacketError') and error != 0:
            self.log(f"[SCServo Error] {self.identifier} {self.packetHandler.getRxPacketError(error)}")
            # Attempting to clear error by toggling torque off and on
            comm_result, error = self.packetHandler.write1ByteTxRx(self.portHandler, self.index, ADDR_TORQUE_ENABLE, 0)
            time.sleep(0.1)
            # comm_result, error = self.packetHandler.write1ByteTxRx(self.portHandler, self.index, ADDR_TORQUE_ENABLE, )
            # self._sc_write(type, value)
            # # Typical address for Present Load is 54 (1 byte), but check your servo's manual
            # ADDR_SCS_PRESENT_LOAD = 54
            # ADDR_SCS_PRESENT_POSITION = 56
            # ADDR_SCS_PRESENT_SPEED = 58
            # # Read present load
            # load, load_comm_result, load_error = self.packetHandler.read1ByteTxRx(self.portHandler, self.index, ADDR_SCS_PRESENT_LOAD)
            # # Read present position (2 bytes)
            # pos, pos_comm_result, pos_error = self.packetHandler.read2ByteTxRx(self.portHandler, self.index, ADDR_SCS_PRESENT_POSITION)
            # # Read present speed (2 bytes)
            # speed, speed_comm_result, speed_error = self.packetHandler.read2ByteTxRx(self.portHandler, self.index, ADDR_SCS_PRESENT_SPEED)
            # self.log(f"[SCServo][{self.identifier}] Error context: load={load} (comm_result={load_comm_result}, error={load_error}), position={pos} (comm_result={pos_comm_result}, error={pos_error}), speed={speed} (comm_result={speed_comm_result}, error={speed_error})")
        return comm_result == COMM_SUCCESS and error == 0
    
    def move_degrees(self, degrees):
        if self.range_degrees is None:
            self.log(f"Servo {self.identifier} does not have range_degrees set, cannot move by degrees", level='error')
            return
        # Convert degrees to position value based on range, adjusting RELATIVE to current position
        self.pos = self.get_position()  # Update current position before calculating new position
        if self.range is not None and self.pos is not None:
            # Calculate how many position units correspond to the degree change
            units_per_degree = (self.range[1] - self.range[0]) / self.range_degrees
            position_delta = degrees * units_per_degree
            new_position = round(self.pos + position_delta)
            # Clamp to range
            if new_position < self.range[0]:
                new_position = self.range[0]
            elif new_position > self.range[1]:
                new_position = self.range[1]
            if self.range_degrees > 0:
                pc_move = round((degrees / self.range_degrees) * 100)
                self.log(f"Moving servo {self.identifier} by {degrees} degrees (position {self.pos} -> {new_position} | {pc_move}% of range)")
                self.move(new_position)

    def move(self, position, speed=None, acceleration=None, delay=0, **kwargs):
        """
        Add a move request to the queue.
        :param position: Target position
        :param speed: Optional speed override
        :param acceleration: Optional acceleration override
        :param delay: Optional delay in seconds before executing (for animation)
        """
        self._move_queue.append({
            'position': position,
            'speed': speed if speed is not None else self.speed,
            'acceleration': acceleration if acceleration is not None else self.acceleration,
            'timestamp': time.time(),
            'delay': delay,
        })

    def loop(self):
        """Called every system loop cycle to drain the move queue."""
        self._process_queue()

    def _process_queue(self, **kwargs):
        """
        Process the next item in the move queue if the servo is not moving.
        Called every loop cycle.
        """
        if not self._move_queue:
            return
        if self.is_moving():
            return
        next_item = self._move_queue[0]
        if time.time() - next_item['timestamp'] >= next_item['delay']:
            self._move_queue.popleft()
            self._do_move(next_item['position'], next_item['speed'], next_item['acceleration'])

    def _do_move(self, position, speed=None, acceleration=None):
        """
        Move the servo to an absolute position.
        :param position: Position to move to
        :param speed: Optional speed override
        :param acceleration: Optional acceleration override
        """
        if position is None:
            self.log(f"Position is None for servo {self.identifier}, cannot move", level='error')
            return
        
        speed = speed if speed is not None else self.speed
        acceleration = acceleration if acceleration is not None else self.acceleration

        # self.log(f"(MOVE) Moving servo {self.identifier} from {self.pos} to position {position} for range {self.range}")
        if position < self.range[0] or position > self.range[1]:
            self.log(f"Position {position} out of range ({self.range[0]}-{self.range[1]})", level='error')
            return
        
        # Write STServo goal position
        if self.model.startswith('ST'):
            sts_comm_result, sts_error = self.packetHandler.WritePosEx(self.index, position, speed, acceleration)
            if not self.handle_errors(sts_comm_result, sts_error):
                self.log(f"Moved ST servo {self.identifier} from {self.pos} to position {position}")
                self.pos = position  # Update current position
        elif self.model.startswith('SC'):
            if (
                self._sc_write(ADDR_TORQUE_ENABLE, 1) and
            self._sc_write(ADDR_SCS_GOAL_ACC, acceleration) and
            self._sc_write(ADDR_SCS_GOAL_SPEED, speed) and
            self._sc_write(ADDR_SCS_GOAL_POSITION, position)):
                self.log(f"Moved SC servo {self.identifier} from {self.pos} to position {position} in range {self.range}  at speed {speed} and acceleration {acceleration} ")
                self.pos = position  # Update current position
            else:
                self.log(f"Failed to move SC servo {self.identifier} to position {position}", level='error')
    
    def move_relative(self, delta):
        """
        Move the servo relative to its current position.
        :param delta: Change in position (can be negative)
        """
        # self.log(f"Moving servo {self.identifier} from {self.pos} by delta {delta}")
        new_position = round(self.pos + delta)
        if new_position < self.range[0] or new_position > self.range[1]:
            self.log(f"Position {new_position} out of range ({self.range[0]}-{self.range[1]}). Adjusting", level='warning')
            new_position = self.range[0] if new_position < self.range[0] else self.range[1]
        
        # Move to new position
        self.move(new_position)
        
        
    def is_moving(self):
        if self.get_moving() == 1:
            return True
        elif abs(self.pos - self.get_position()) > 15:
            print(f"Warning: Servo {self.identifier} is not reporting as moving but position {self.get_position()} does not match target position {self.pos}")
        return False
        
    def get_position(self):
        """
        Get the current position of the servo.
        """
        if self.model.startswith('ST'):
            # Read STServo present position
            sts_present_position, sts_present_speed, sts_comm_result, sts_error = self.packetHandler.ReadPosSpeed(self.index)
            if not self.handle_errors(sts_comm_result, sts_error):
                # self.log("[ID:%03d] PresPos:%d PresSpd:%d" % (self.index, sts_present_position, sts_present_speed))
                return sts_present_position
        else:
            return self.sc_get_position_speed('position')
    
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
        
        
    def sc_get_position_speed(self, pos_or_speed):
        # Read SCServo present position
        scs_present_position_speed, scs_comm_result, scs_error = self.packetHandler.read4ByteTxRx(self.portHandler, self.index, ADDR_SCS_PRESENT_POSITION)
        if not self.handle_errors(scs_comm_result, scs_error):
            scs_present_position = SCS_LOWORD(scs_present_position_speed)
            scs_present_speed = SCS_HIWORD(scs_present_position_speed)
            if pos_or_speed == 'position':
                return scs_present_position
            elif pos_or_speed == 'speed':
                return SCS_TOHOST(scs_present_speed, 15)
    
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
    
    def get_pose_value(self, pose_name):
        """
        Returns the position value for the given pose name from self.poses.
        """
        if not self.poses:
            return None
        for pose in self.poses:
            if pose_name in pose:
                return pose[pose_name]
        return None  # or raise an exception if preferred

    def calibrate(self):
        """
        Move each servo to capture min and max positions for calibration.
        """
        self.log(f"Move servo {self.identifier} to minimum position and press any key...")
        getch()  # Waits for a single key press
        min = self.get_position()
        self.log(f"Captured minimum position: {min}")
        self.log(f"Move servo {self.identifier} to maximum position and press any key...")
        getch()  # Waits for a single key press
        max = self.get_position()
        self.log(f"Captured maximum position: {max}")
        self.range = (min, max)
        if self.start is not None and (self.start < min or self.start > max):
            self.start = (min + max) // 2
            self.log(f"Start position {self.start} out of new range, setting to midpoint {self.start}")
        self.log(f"Updated range for {self.identifier}: {self.range}. Start position: {self.start}")

    def calibrate_dynamic(self):
        """
        Continuously log the current position to help with manual calibration.
        Store min an max as they are found.
        Complete on key press. and store in self.range
        """
        self.log(f"Calibrating servo {self.identifier}. Move the servo to find min and max positions. Press any key to finish...")
        self.detach()
        min_pos = None
        max_pos = None
        try:
            while True:
                pos = self.get_position()
                if pos is None:
                    self.log(f"Failed to get position for servo {self.identifier}", level='warning')
                    continue
                if min_pos is None or pos < min_pos:
                    min_pos = pos
                if max_pos is None or pos > max_pos:
                    max_pos = pos
                # Print on the same line, pad with spaces to clear previous content
                # (4095 = 360 degrees, so 1264 = 111 degrees)
                range_degrees = (360/4095)*(max_pos - min_pos) if min_pos is not None and max_pos is not None else 'N/A'
                print(f"\rCurrent position: {pos}, Min: {min_pos}, Max: {max_pos} Range(deg): {range_degrees}", end='', flush=True)
                time.sleep(0.05)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.read(1)  # Consume the key so buffer is cleared
                    break
        except KeyboardInterrupt:
            # No need to handle as this is to allow changing selected servo
            pass
        print()  # Move to next line after loop
        if min_pos is not None and max_pos is not None:
            self.range = (min_pos, max_pos)
            self.log(f"Calibration complete for {self.identifier}. Range: {self.range}")
        else:
            self.log(f"No positions recorded during calibration for {self.identifier}.", level='warning')
            
        if self.start is not None and (self.start < min_pos or self.start > max_pos):
            self.start = (min_pos + max_pos) // 2
            self.log(f"Start position {self.start} out of new range, setting to midpoint {self.start}")

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




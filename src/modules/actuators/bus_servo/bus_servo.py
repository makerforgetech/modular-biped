#!/usr/bin/env python

import collections
import sys
import select
import time
from modules.base_module import BaseModule
from modules.actuators.bus_servo.libraries.factory import BusServoFactory
class Servo(BaseModule):
    def __init__(self, **kwargs):
        """
        Servo class
        """
        self.backend = kwargs.get('backend', 'waveshare')
        self.identifier = kwargs.get('name')
        self.model = kwargs.get('model', 'ST')
        self.index = kwargs.get('id')
        self.range = kwargs.get('range')
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
        poses_list = kwargs.get('poses', [])
        self.poses = {list(pose.keys())[0]: list(pose.values())[0] for pose in poses_list}

        # Backend selection
        
        self.backend_servo = BusServoFactory.create(
            backend=self.backend,
            model=self.model,
            servo_id=self.index,
            port=self.port,
            baudrate=self.baudrate,
            range=self.range,
        )
        
    def detach(self):
        # Detach servo using backend
        self.backend_servo.detach()
    
    def exit(self):
        self.detach()
        self.backend_servo.exit()

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
        if position < self.range[0] or position > self.range[1]:
            self.log(f"Position {position} out of range ({self.range[0]}-{self.range[1]})", level='error')
            return
        # Delegate to backend
        self.backend_servo.move_to(position, unit='degrees')
        self.pos = position
    
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
        if self.backend_servo.get_moving() == 1:
            return True
        elif abs(self.pos - self.get_position()) > 2:
            print(f"Warning: Servo {self.identifier} is not reporting as moving but position {self.get_position()} does not match target position {self.pos}")
        return False
        
    def get_position(self):
        """
        Get the current position of the servo.
        """
        return self.backend_servo.get_position(unit='degrees')
    
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
                range_degrees = max_pos - min_pos if min_pos is not None and max_pos is not None else 'N/A'
                print(f"\rCurrent position: {pos}, Min: {min_pos}, Max: {max_pos} Range: {range_degrees}", end='', flush=True)
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

    



from random import choice, randint
import time
from modules.base_module import BaseModule
from modules.config import Config
from time import sleep

class Personality(BaseModule):

    def __init__(self, **kwargs):
        self.eye = 'blue'
        self.object_reaction_end_time = None

        # Configurable interval range
        self.min_interval = kwargs.get('min_interval', 20)  # Default minimum 20 seconds
        self.max_interval = kwargs.get('max_interval', 60)  # Default maximum 60 seconds

        self.motion_last_detected = None # time since last motion detected
        self.last_vision_time = None
        self.next_action_time = self.calculate_next_action_time()
        self.last_status_time = None
        self.last_serial_time = None

        # Initialize status LED colors (default to 'off')
        self.led_colors = ['off'] * 5

        self.display_background = 'black'
        self.temperature = None
        self.start_time = time.time()
        self.display_change = time.time()
        self.display_state = 0
        
        self.current_hz = 0

        self.imu = {} # Set in main.py
        self.vision = None # Set in main.py
        self.euler = None
        self.balance_enabled = kwargs.get('balance_enabled', True)
        self.chicken_head_enabled = kwargs.get('chicken_head_enabled', False)
        self.track_people = kwargs.get('track_people', True) # Uses vision data to track detected people with the eyes, and optionally neck servos.
        self.track_people_servos = kwargs.get('track_people_servos', False) # Moves neck servos to track detected people.
        self.one_leg_balance_enabled = kwargs.get('one_leg_balance_enabled', True)
        self.servos = {} # Set in main.py
        self.pose = None

        # Define possible actions
        self.actions = [
            # self.braillespeak,
            self.eye_blink,
            self.eye_blink,
            # self.move_antenna,
        ]
        
    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('system/loop/1', self.loop_second)
        self.subscribe('system/loop/10', self.loop_10)
        if self.track_people:
            self.subscribe('vision/detections', self.handle_vision_detections) # Enable after testing north facing
        self.subscribe('gpio/motion', self.update_motion_time)
        self.subscribe('serial', self.track_serial_idle)
        self.subscribe('system/temperature', self.handle_temperature)
        # self.subscribe('system/loop/10', self.test_servos)
        # self.publish('gpio/laser', state=True) # Turn on laser if no one has been detected
        self.subscribe('telegram/received', self.handle_user_message)
        self.subscribe('ai/response', self.handle_ai_response)
        self.subscribe('system/debug/log_hz', self.update_current_hz)
        # if True: # Bypass pubsub
        #     self.subscribe('system/loop/1', self.balance)
        # else:
        #     # self.subscribe('imu/imu_head/data', self.handle_imu_data)
        #     self.subscribe('imu/imu_body/data', self.handle_imu_data)
        # self.publish('gpio/laser', state=True) # Turn on laser if no one has been detected

    def test_servos(self):
        
        self.log("Testing neck tilt servos")
        # Reset
        self.publish('servo:neck_pan:mvabs', position=200)
        self.publish('servo:neck_tilt:mvabs', position=511)
        self.publish('servo:neck_tilt2:mvabs', position=511)
        time.sleep(2)
        self.publish('servo:neck_tilt:mv', delta=-150)
        self.publish('servo:neck_tilt2:mv', delta=150)
        time.sleep(2)
        self.publish('servo:neck_tilt:mv', delta=300)
        self.publish('servo:neck_tilt2:mv', delta=-300)
        time.sleep(2)
        self.publish('servo:neck_pan:mv', delta=200)
        time.sleep(2)
        self.publish('servo:neck_pan:mv', delta=-400)
        self.log("Neck tilt servos test complete")
    
    def output_current_pose(self):
        """Get current pose of all servos and return as a json object."""
        # Iterate over each self.servos and get current position
        
        for name, servo in self.servos.items():
            servo.detach() # Disable torque to get accurate position reading without resistance
        while True:
            pose = {}
            for name, servo in self.servos.items():
                try:
                    pos = servo.get_position()
                    pose[name] = pos
                except Exception as e:
                    self.log(f"Error getting position for servo {name}: {e}", level='error')
            print(f"\r{pose}    ", end='', flush=True)
            time.sleep(1)
    
    def update_current_hz(self, hz):
        self.current_hz = hz
        
    def chicken_head(self):
        """ Using self.imu['head'] data (if present), rotate the head to face the same direction (0 degrees from get_euler()[1]). """
        if not self.chicken_head_enabled or 'head' not in self.imu:
            return
        euler = self.imu['head'].get_euler()
        yaw = euler[0]
        pitch = euler[1]    
        print(f"Current head pitch: {yaw}, pitch: {pitch}")
        if yaw < 180:
            zero_yaw = -yaw
        else:
            zero_yaw = 360 - yaw # Prevent turning more than 180 degrees in either direction
            
        print(f"Pitch: {pitch}, Angle to zero yaw: {zero_yaw}")
        if abs(pitch) > 5:
            self.servos['neck_tilt'].move_degrees(pitch)
        if abs(zero_yaw) > 5:
            self.servos['neck_pan'].move_degrees(zero_yaw)
            
    def one_leg_balance(self):
        """ Use body IMU data to move legs into a one legged stance by lifting one leg and adjusting the other leg and body to maintain balance. """
        if not self.one_leg_balance_enabled or 'body' not in self.imu:
            return
        euler = self.imu['body'].get_euler()
        roll = euler[2]
        
        if abs(roll) < 8:
            if abs(roll) < 3:
                return   # No need to adjust for small angles
            # Return to center pos
            self.servos['leg_l_tilt'].move(self.servos['leg_l_tilt'].start)
            self.servos['leg_r_tilt'].move(self.servos['leg_r_tilt'].start)
            return
        print(f"Current body roll: {roll}")
        # This should just show one leg extend under the body, and the other knee bending. For demo only
        if roll > 0:
            # self.servos['leg_l_knee'].move_degrees(-90)
            self.servos['leg_l_tilt'].move_degrees(roll)
            self.servos['leg_r_tilt'].move(self.servos['leg_r_tilt'].start)
            # self.servos['leg_r_knee'].move_degrees(90)
            pass
        else:
            self.servos['leg_r_tilt'].move_degrees(roll)
            # self.servos['leg_l_tilt'].calibrate_to_center()
            self.servos['leg_l_tilt'].move(self.servos['leg_l_tilt'].start)
            # self.servos['leg_r_knee'].move_degrees(-90)
            # self.servos['leg_r_tilt'].move_degrees(-pitch)
            # self.servos['leg_l_knee'].move_degrees(90)

    def balance(self):
        """Use head and body IMU data to maintain balance by adjusting leg servos."""
        if not self.balance_enabled or 'body' not in self.imu:
            return
        euler = self.imu['body'].get_euler()
        # if euler has changed significantly since last update, adjust servos
        if self.euler is None or any(abs(e - self.euler[i]) > 1 for i, e in enumerate(euler)):
            self.euler = euler
            pitch = euler[1]
            if abs(pitch) < 2:
                return  # No need to adjust for small angles
            # print(f"Angle to move: {pitch}")
            self.servos['leg_l_hip'].move_degrees(-pitch) 
            self.servos['leg_r_hip'].move_degrees(pitch)
    
    def handle_user_message(self, user_id=None, message=None):
        print(f"Received message from user {user_id}: {message}")
        self.publish('ai/input', text=message)
        self.publish('telegram/respond', user_id=user_id, message=f"Echo: {message}")
        
    def handle_ai_response(self, response=None):
        print(f"Received AI response: {response}")
        self.publish('telegram/respond', message=response, user_id=None)
    
    def cycle_display(self):
        """Cycle through different display states. Display time, temperature, uptime, tilt, and Hz for 5 seconds each."""
        states = ['time', 'temperature', 'uptime', 'tilt', 'hz', 'pose']
        if self.display_change and time.time() - self.display_change >= 5:
            self.display_change = time.time()
            self.display_state = (self.display_state + 1) % len(states)

        if self.display_state == 0:
            # Display current time
            now = time.localtime()
            time_str = time.strftime("%H:%M:%S", now)
            self.publish('display/body/text', text=f"{time_str}", font_size=26)
        elif self.display_state == 1:
            self.publish('display/body/text', text=f"{self.temperature if self.temperature is not None else '?'}°C", font_size=26)
        elif self.display_state == 2:
            uptime_seconds = int(time.time() - self.start_time)
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            self.publish('display/body/text', text=f"Uptime\n{uptime_str}", font_size=14)
        elif self.display_state == 3:
            if self.imu and self.imu.get('body'):
                tilt = self.imu['body'].get_euler()[1]
                self.publish('display/body/text', text=f"T: {tilt}", font_size=26)
            else:
                self.publish('display/body/text', text=f"T: No Data", font_size=26)
        elif self.display_state == 4:
            self.publish('display/body/text', text=f"{self.current_hz}Hz", font_size=20)
        elif self.display_state == 5:
            self.publish('display/body/text', text=f"{self.pose}", font_size=20)

    def loop_10(self):
        # loop 3 times:
        # for i in range(3):
        #     self.servos['leg_l_ankle'].move(1000, speed=0)
        #     self.servos['leg_l_ankle'].move(1500, speed=0) 
        # self.servos['leg_l_ankle'].move_degrees(50)
        # self.scan_vision()
        # self.output_current_pose()
        # self.publish('servo/pose', pose_name='wave_1') # For testing pose movement
        # time.sleep(1)
        # current_pose = self.estimate_current_pose()
        # if current_pose not in self.servos['leg_r_tilt'].poses:
        #     return
        # if current_pose == 'sit':
            # self.publish('servo/pose', pose_name='wave_1') # For testing pose movement
            # self.publish('servo/pose', pose_name='wave_2') # For testing pose movement
            # self.publish('servo/pose', pose_name='wave_1') # For testing pose movement
            # self.publish('servo/pose', pose_name='wave_2') # For testing pose movement
            # self.publish('servo/pose', pose_name='sit') # For testing pose movement
            # self.pose = 'sit'
        # elif current_pose == 'sit_edge':
        #     self.pose = 'sit_edge_swing_l'
        # elif current_pose == 'sit_edge_swing_l':
        #     self.pose = 'sit_edge_swing_r'
        # elif current_pose == 'sit_edge_swing_r':
        #     self.pose = 'sit_edge'
        # elif current_pose == 'legs_forward':
        #     self.pose = 'sit'
        # self.publish('servo/pose', pose_name=self.pose) # For testing pose movement
        pass
    
    def loop(self):
        pass
        
    def loop_second(self):
        now = time.time()
        self.cycle_display()
        self.balance()
        self.chicken_head()
        self.one_leg_balance()
        self.estimate_current_pose()
        
        # Handle ongoing object reaction
        if self.object_reaction_end_time and now >= self.object_reaction_end_time:
            self.publish('led', identifiers=[
                'right', 'top_right', 'top_left', 'left', 
                'bottom_left', 'bottom_right'
            ], color="off")
            self.object_reaction_end_time = None

        # self.update_eye()
        self.random_neopixel_status()

        # Check if it's time for the next action
        if now >= self.next_action_time:
            action = choice(self.actions)
            action()
            self.next_action_time = self.calculate_next_action_time()

        # If serial has been idle for more than 10 seconds, call random_animation()
        if self.last_serial_time and (now - self.last_serial_time > 10):
            self.random_animation()
    
    def estimate_current_pose(self):
        """ Identify current pose by matching servo positions to known poses in config. Do not require exact match of values, but 'close enough' check"""
        current_pose = {}
        for name, servo in self.servos.items():
            try:
                pos = servo.pos # setting as servo.pos because servo.get_position() is not showing the expected value. Will investigate
                # actual_pos = servo.get_position()
                # if pos != actual_pos:
                #     self.log(f"Warning: Position mismatch for servo {name}. servo.pos: {pos}, get_position(): {actual_pos}. Diff: {pos - actual_pos}", level='warning')
                current_pose[name] = pos
            except Exception as e:
                self.log(f"Error getting position for servo {name}: {e}", level='error')
        # print(f"Current positions: {current_pose}")
        try:
            for pose_name, pose_values in self.servos['leg_r_tilt'].poses.items():
                if all(abs(current_pose.get(servo_name, 0) - pose_value) < 100 for servo_name, pose_value in pose_values.items()):
                    # print(f"Current pose is approximately: {pose_name}")
                    self.pose = pose_name
                    return pose_name
        except Exception as e:
            self.log(f"Error estimating current pose: {e}", level='warning')
        # print("Current pose does not match any known poses")
        return None
        
    
    def handle_temperature(self, value):
        """Handle temperature updates."""
        self.temperature = float(value)
        temprgba = self.temperature_to_rgba(self.temperature)
        # self.log(f"Handling temperature: {temp} color: {temprgba}")
        if self.temperature > 70 and self.display_background != temprgba:
            self.publish('display/background', color=temprgba)
            self.display_background = temprgba
        elif self.display_background != 'black':
            self.publish('display/background', color='black')
            self.display_background = 'black'
            
    
    def random_animation(self):
        self.publish('animate', action='level_neck')
        animations = [
            'head_shake',
            'head_nod',
            'head_left',
            'head_right',
            # 'look_down',
            'look_up'
        ]
        animation = choice(animations)
        self.log(f"Random animation triggered: {animation}")
        self.publish('animate', action=animation)

    # Calculate the next action time
    def calculate_next_action_time(self):
        interval = randint(self.min_interval, self.max_interval)
        return time.time() + interval

    # Braillespeak: Outputs short messages as tones
    def braillespeak(self):
        messages = ["Hi", "Hello", "Hai", "Hey"]
        msg = choice(messages)
        self.publish('speak', msg=msg)
        self.log(f"Braillespeak triggered: {msg}")

    # Buzzer: Outputs a specific tone
    def buzzer_tone(self):
        frequency = randint(300, 1000)  # Random frequency between 300Hz and 1000Hz
        length = round(randint(1, 5) / 10, 1)  # Random length between 0.1s and 0.5s
        self.publish('buzz', frequency=frequency, length=length)
        self.log(f"Buzzer tone triggered: {frequency}Hz for {length}s")

    # Buzzer: Plays one of two predefined tunes
    def buzzer_song(self):
        songs = ["happy birthday", "merry christmas"]
        song = choice(songs)
        self.publish('play', song=song)
        self.log(f"Buzzer song triggered: {song}")

    # Neopixels: Toggles random status LEDs
    def random_neopixel_status(self):
        now = time.time()
        if not self.last_status_time or (now - self.last_status_time > 3):
            self.last_status_time = now
            color = choice(["red", "green", "blue", "white_dim", "purple", "yellow", "orange", "pink"])
            self.publish('led', identifiers=[0], color=color)
            for i in range(4, 0, -1):
                if i+1 < 5:
                    self.led_colors[i] = self.led_colors[i-1]
            for i in range(1, 5):
                self.publish('led', identifiers=[i], color=self.led_colors[i])
            self.led_colors[0] = color
            self.log(message=f"Neopixel status triggered set to {color}", level='debug')

    # Antenna: Moves to a random angle between -40 and 40 degrees
    def move_antenna(self):
        angle = randint(-40, 40)
        self.publish('piservo/move', angle=angle)
        self.log(f"Antenna moved to angle: {angle}")
        
    def eye_blink(self):
        """Simulates an eye blink by publishing a blink event."""
        self.publish('eye/blink')
        self.log("Eye blink triggered")

    def scan_vision(self):
        if self.vision is None:
            return
        matches = self.vision.scan()
        # print(f"Vision matches: {matches}")
        self.handle_vision_detections(matches)

    # Vision: Handles detected objects
    def handle_vision_detections(self, matches):
        now = time.time()
        # if there are matches and the object reaction end time is in the past
        if matches and len(matches) > 0 and (self.object_reaction_end_time is None or now >= self.object_reaction_end_time):
            # get all matches with category 'person'
            people = [match for match in matches if match['category'] == 'person']
            # if more than one person, choose the largest one (closest)
            if len(people) > 1:
                people.sort(key=lambda x: x['bbox'][2]*x['bbox'][3],
                            reverse=True)  # Sort by bounding box area 
            if len(people) > 0:
                # self.publish('gpio/laser', state=False)  # Turn off laser when person detected
                self.track_match(people[0]['bbox'])
                self.last_vision_time = now
                # Set the object reaction end time to 0.5 seconds from now
            # self.log(f"Vision detected objects: {matches}", 'debug')
            self.object_reaction_end_time = now + 0.5
    
    def track_match(self, match):
        screen = (240, 240)  # TFT display size
        camera_size = (640, 480)  # Camera resolution
        # log/info: [Personality.handle_vision_detections:135] Vision detected objects: 
        # [{'category': 'person', 'confidence': '0.5625', 'bbox': (7, 199, 172, 278), 'distance_x': -227, 'distance_y': -26}, {'category': 'airplane', 'confidence': '0.5625', 'bbox': (190, 61, 149, 106), 'distance_x': -56, 'distance_y': -170}]
        # Example output:  
        # Person detected at coordinates: (84.5, 239.0)
        # Converted coordinates: (31, 119)
        
        # Get center position from match.bbox. 
        # Assuming bbox is in the format [x_min, y_min, x_width, y_width]
        center_pos_x = match[0] + (match[2] / 2)
        center_pos_y = match[1] + (match[3] / 2)
        
        # print(f"Person detected at coordinates: ({center_x}, {center_y})")
        
        # Convert to tft display coordinates where (0,0) is the top left corner and (240,240) is the bottom right corner
        # Assuming original coordinates are in a 640x480 space
        center_x = int((center_pos_x/camera_size[0]) * screen[0]) 
        center_y = int((center_pos_y/camera_size[1]) * screen[1])
        
        # print(f"Converted coordinates: ({center_x}, {center_y})")
        
        # Rotate 90 degrees clockwise
        # center_x, center_y = 240 - center_y, center_x
        # Rotate 90 degrees anticlockwise
        center_x, center_y = center_y, screen[0] - center_x
        
        # flip the y-axis to match the TFT display coordinates
        center_x = screen[0] - center_x
        
        # scale movements so that it only moves 50% of the distance from the center of the screen
        center_x = int(center_x * 0.5) + screen[0] // 4
        center_y = int(center_y * 0.5) + screen[1] // 4
        
        # print(f"Rotated coordinates: ({center_x}, {center_y})")
        self.publish('eye/look', coordinates=(center_x, center_y))
        
        if not self.track_people_servos:
            return
        
        track_threshold = [15, 15] # Minimum angle change to trigger servo movement
        
        # Move pan servo based on center_pos_x position relative to camera_size
        pan_angle = int(((center_pos_x - (camera_size[0] / 2)) / (camera_size[0] / 2)) * 40)  # Scale to -40 to 40 degrees
        if abs(pan_angle) > track_threshold[0]:  # Only move if the angle is greater than 5 degrees to avoid jitter
            self.log(f"Moving neck pan to {pan_angle} degrees based on detected object position")
            self.servos['neck_pan'].move_degrees(pan_angle)
            
        # Move tilt servo based on center_pos_y position relative to camera_size
        # Focus on the top of the bounding box in the Y axis
        top_section_y = match[1] + 0.33 * match[3]
        tilt_angle = int(((top_section_y - (camera_size[1] / 2)) / (camera_size[1] / 2)) * 40)  # Scale to -40 to 40 degrees
        if abs(tilt_angle) > track_threshold[1]:  # Only move if the angle is greater than 5 degrees to avoid jitter
            self.log(f"Moving neck tilt to {tilt_angle} degrees based on detected object position")
            self.servos['neck_tilt'].move_degrees(-tilt_angle)

    # Motion: Updates the last motion time
    def update_motion_time(self, value):
        self.motion_last_detected = value

    # Updates the middle eye LED based on the current state
    def update_eye(self):
        now = time.time()
        if self.last_vision_time and (now - self.last_vision_time <= 3):
            self.publish('eye', color='green')
        elif self.motion_last_detected and (self.motion_last_detected > 30):
            self.publish('eye', color='dark_gray')
        else:
            self.publish('eye', color='blue')

    def track_serial_idle(self, type, identifier, message):
        self.last_serial_time = time.time()

    def temperature_to_rgba(self, temp, min_temp=70, max_temp=90):
        """
        Map a temperature value in the range [min_temp, max_temp] to an RGBA color from black to red.
        Returns a tuple (R, G, B, A).
        """
        # Clamp temperature to the range
        temp = max(min_temp, min(max_temp, temp))
        # Normalize to 0.0 - 1.0
        norm = (temp - min_temp) / (max_temp - min_temp)
        r = int(255 * norm)
        g = 0
        b = 0
        a = 255
        return (r, g, b, a)
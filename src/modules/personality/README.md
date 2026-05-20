# Personality Module Documentation

## Overview

The `Personality` module is designed to add personality and interactive behaviors to the robot. It subscribes to various events such as motion detection, serial communication, and vision detections, and responds with actions like animations, LED changes, and sounds. This documentation outlines the current functionality and how it interacts with other modules.

## Configuration

Before using the `Personality` module, you need to configure it in the `config/personality.yml` file. Below is an explanation of the configuration options:

```yaml
personality:
  enabled: true  # Set to true to enable the Personality module
  path: modules.personality.Personality  # Path to the Personality class
  config:
    min_interval: 20  # Minimum interval between actions in seconds
    max_interval: 60  # Maximum interval between actions in seconds
```

### Dependencies

After enabling the module, run `./install.sh` to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

## Usage

### Initializing the Personality Module

When the module is enabled in the config YAML, the `Personality` class is automatically imported and initialized.

### Subscribing to Topics

The `Personality` module subscribes to various topics to receive events and trigger actions. Here’s an example of how to subscribe to topics:

```python
def setup_messaging(self):
    """Subscribe to necessary topics."""
    self.subscribe('system/loop/1', self.loop)
    self.subscribe('vision/detections', self.handle_vision_detections)
    self.subscribe('motion', self.update_motion_time)
    self.subscribe('serial', self.track_serial_idle)
```

### Loop Method

The `loop` method is called periodically to handle ongoing reactions and trigger new actions based on the current state and timing intervals.

```python
def loop(self):
    # Handle ongoing object reaction
    if self.object_reaction_end_time and datetime.now() >= self.object_reaction_end_time:
        self.publish('led', identifiers=[
            'right', 'top_right', 'top_left', 'left', 
            'bottom_left', 'bottom_right'
        ], color="off")
        self.object_reaction_end_time = None

    # Update the middle eye LED based on conditions
    self.update_middle_eye_led()
    
    self.random_neopixel_status()

    # Check if it's time for the next action
    if datetime.now() >= self.next_action_time:
        action = choice(self.actions)
        action()
        self.next_action_time = self.calculate_next_action_time()
    
    # If serial has been idle for more than 10 seconds, call random_animation()
    if self.last_serial_time and datetime.now() - self.last_serial_time > timedelta(seconds=10):
        self.random_animation()
```

### Actions

The `Personality` module defines various actions that can be triggered, such as animations, sounds, and LED changes.

#### Random Animation

```python
def random_animation(self):
    animations = [
        'head_shake',
        'head_left',
        'head_right',
        'wake',
        'look_down',
        'look_up',
        'celebrate'
    ]
    animation = choice(animations)
    self.log(f"Random animation triggered: {animation}")
    self.publish('animate', action=animation)
```

#### Braillespeak

```python
def braillespeak(self):
    messages = ["Hi", "Hello", "Hai", "Hey"]
    msg = choice(messages)
    self.publish('speak', msg=msg)
    self.log(f"Braillespeak triggered: {msg}")
```

#### Buzzer Tone

```python
def buzzer_tone(self):
    frequency = randint(300, 1000)  # Random frequency between 300Hz and 1000Hz
    length = round(randint(1, 5) / 10, 1)  # Random length between 0.1s and 0.5s
    self.publish('buzz', frequency=frequency, length=length)
    self.log(f"Buzzer tone triggered: {frequency}Hz for {length}s")
```

#### Buzzer Song

```python
def buzzer_song(self):
    songs = ["happy birthday", "merry christmas"]
    song = choice(songs)
    self.publish('play', song=song)
    self.log(f"Buzzer song triggered: {song}")
```

#### Random Neopixel Status

```python
def random_neopixel_status(self):
    if not self.last_status_time or datetime.now() - self.last_status_time > timedelta(seconds=3):
        self.last_status_time = datetime.now()
        color = choice(["red", "green", "blue", "white_dim", "purple", "yellow", "orange", "pink"])
        self.publish('led', identifiers=[0], color=color)
        for i in range 4, 0, -1):
            if i+1 < 5:
                self.led_colors[i] = self.led_colors[i-1]
        for i in range(1, 5):
            self.publish('led', identifiers=[i], color=self.led_colors[i])
        self.led_colors[0] = color
        self.log(message=f"Neopixel status triggered set to {color}", level='debug')
```

#### Random Neopixel Eye

```python
def random_neopixel_eye(self):
    positions = [
        'right', 'top_right', 'top_left', 'left', 
        'bottom_left', 'bottom_right'
    ]
    position = choice(positions)
    color = choice(["white_dim"])
    self.publish('led', identifiers=positions, color=color)
    self.log(f"Neopixel eye ring set to {color}")
```

#### Move Antenna

```python
def move_antenna(self):
    angle = randint(-40, 40)
    self.publish('piservo/move', angle=angle)
    self.log(f"Antenna moved to angle: {angle}")
```

### Handling Vision Detections

The `handle_vision_detections` method processes detected objects and triggers reactions.

```python
def handle_vision_detections(self, matches):
    if matches and len(matches) > 0 and (self.object_reaction_end_time is None or datetime.now() >= self.object_reaction_end_time):
        self.log(f"Vision detected objects: {matches}")
        self.last_vision_time = datetime.now()
        self.random_neopixel_eye()
        self.object_reaction_end_time = datetime.now() + timedelta(seconds=3)
```

### Updating Motion Time

The `update_motion_time` method updates the last motion time.

```python
def update_motion_time(self):
    self.last_motion_time = datetime.now()
```

### Updating Middle Eye LED

The `update_middle_eye_led` method updates the middle eye LED based on the current state.

```python
def update_middle_eye_led(self):
    now = datetime.now()
    if self.last_vision_time and now - self.last_vision_time <= timedelta(seconds=30):
        self.publish('led', identifiers='middle', color='green')
    elif now - self.last_motion_time > timedelta(seconds=30):
        self.publish('led', identifiers='middle', color='red')
    else:
        self.publish('led', identifiers='middle', color='blue')
```

### Tracking Serial Idle

The `track_serial_idle` method tracks the last serial communication time.

```python
def track_serial_idle(self, type, identifier, message):
    self.last_serial_time = datetime.now()
```

## Customization

The `Personality` module can be modified to meet specific requirements for different implementations. You can add new actions, change the intervals, or modify the existing behaviors to suit your needs.

## Conclusion

The `Personality` module provides a comprehensive framework for adding personality and interactive behaviors to the robot. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and customize the `Personality` module in your projects.
# XboxController & ControllerHandler Documentation

## Overview

The controller system consists of two main classes:
- `XboxController` (in `modules/xbox_controller.py`): Handles low-level gamepad input, normalizes values, and exposes current input status.
- `ControllerHandler` (in `modules/controller_handler.py`): Consumes input from a controller module, maps it to actions/topics, and publishes events to control the robot.

Configuration is provided via YAML files, allowing flexible mapping of controller inputs to robot actions, including support for modifiers, scaling, and multiple mapping sets.

---

## XboxController

**File:** `modules/xbox_controller.py`

### Purpose
- Reads input from a gamepad (e.g., Xbox controller) via `/dev/input/js0`.
- Normalizes button and axis values.
- Exposes current status for consumption by higher-level modules.

### Key Features
- Button and axis names are configurable via YAML.
- Normalized status can be queried at any time.
- Designed to be injected into a handler (e.g., `ControllerHandler`).

---

## ControllerHandler

**File:** `modules/controller_handler.py`

### Purpose
- Maps controller input to robot actions using a YAML-defined mapping.
- Supports modifier buttons for alternate mapping sets.
- Publishes events to the robot's messaging system.

### Key Features
- Supports multiple mapping sets (e.g., `default`, `BTN_TL`, `BTN_TR`), selected by holding modifier buttons.
- Each mapping can define multiple actions per input.
- Actions can include topics, arguments, and modifiers (e.g., scaling).

---

## YAML Configuration

### Example Structure

```yaml
controller:
  enabled: true
  path: 'modules.controller_handler.ControllerHandler'
  config:
    debug: false
    modifier_buttons:
      - BTN_TL
      - BTN_TR
    mapping:
      default:
        BTN_A:
          actions:
            - topic: 'tts'
              args: {msg: 'Hello!'}
        ABS_X:
          actions:
            - topic: 'servo:neck_pan:mv'
              args: {}
              modifier:
                scale: 0.1
              max_delta: 200
      BTN_TL:
        BTN_X:
          actions:
            - topic: 'servo:neck_pan:mv'
              args: {delta: 50}
```

### Mapping Sets
- The top-level keys under `mapping` (e.g., `default`, `BTN_TL`, `BTN_TR`) define different mapping sets.
- The `default` set is used when no modifier buttons are held.
- If one or more modifier buttons are held, the corresponding set is used (e.g., holding `BTN_TL` uses the `BTN_TL` mapping).

### Actions List
- Each input (button or axis) maps to an `actions` list.
- Each action is a dictionary with at least a `topic` (the event to publish) and optional `args` (arguments for the topic).
- Example:
  ```yaml
  BTN_A:
    actions:
      - topic: 'tts'
        args: {msg: 'Hello!'}
  ```

### Modifiers
- Each action can include a `modifier` dictionary to adjust arguments dynamically.
- Common modifier options:
  - `scale`: Multiplies the input value (useful for axes).
  - `mapping`: Maps the input value to a new range (e.g., [0, 240]).
- Example:
  ```yaml
  ABS_X:
    actions:
      - topic: 'servo:neck_pan:mv'
        args: {}
        modifier:
          scale: 0.1
      - topic: 'servo:neck_pan:mv'
        args: {}
        modifier:
          mapping: [-120, 120]
  ```

### Overarching Options
- For axes, you can specify an overarching `start` value at the same level as `actions`:
  ```yaml
  ABS_RY:
    start: -1.0
    actions:
      - topic: 'servo:leg_r_ankle:mv'
        args: {}
  ```
- The handler will use this `start` value to adjust the input before applying thresholds or modifiers. This is useful for inputs where the default start position is not zero.

---

## How It Works

1. The `XboxController` reads and normalizes input, exposing the current status.
2. The `ControllerHandler` subscribes to a loop event and, on each tick:
   - Reads the current status directly from the controller (this dependency is injected after initialization in main.py).
   - Determines which mapping set to use based on active modifier buttons.
   - For each active input, looks up the corresponding actions.
   - Publishes each action's topic with its arguments (applying modifiers as needed).

---

## Adding/Customizing Mappings

- To add a new button or axis mapping, add a new key under the desired mapping set:
  ```yaml
  BTN_B:
    actions:
      - topic: 'tts'
        args: {msg: 'Button B pressed!'}
  ```
- To add multiple actions for a single input, add more items to the `actions` list.
- To use scaling or other modifiers, add a `modifier` dictionary to the action.

---

## Tips
- Use `debug: true` in the config to enable verbose logging for troubleshooting.
- Modifier buttons allow for complex control schemes (e.g., holding `BTN_TL` changes the function of other buttons). Multiple buttons can be combined, e.g. `BTN_TL+BTN_TR`.
- Always test your mappings to ensure the robot responds as expected.


### Enable controller on ubuntu:

I'm not sure what helped with this situation, but I had immense difficulty getting bluetooth working for the Xbox Series S/X controller. I had to upgrade the firmware using this tool on windows 10: https://apps.microsoft.com/detail/9nblggh30xj3?hl=en-GB&gl=GB

In addition, I installed xpadneo:

```
sudo apt install dkms linux-headers-$(uname -r)
git clone https://github.com/atar-axis/xpadneo.git
cd xpadneo
sudo ./install.sh
```

Disabling ERTM may also have been required:
```
sudo nano /etc/modprobe.d/bluetooth.conf

# Add this line and save
options bluetooth disable_ertm=Y

sudo reboot
```

Then use bluetoothctl to test:
```
sudo bluetoothctl
# Turn on agent and set as default
agent on
default-agent

# Start scanning for devices
scan on

# Replace XX:XX:XX:XX:XX:XX with your controller's MAC address
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:X

exit
```

Further adjustments that may have helped:

``` 
# edit /etc/bluetooth/main.conf
[General]
ControllerMode = dual
JustWorksRepairing = confirm
```

The package xboxdrv was also suggested, but I couldn't get that to detect the controller, even once the script was working...

Testing with `jstest /dev/input/js0` (requires `sudo apt-get install joystick`) showed the controller worked, but I could not get the python modules `inputs` or `pygame` to recognise any input from the controller.

In the end I modified the module to poll the /dev/input/js0 stream into python.

---

## Related Files
- `modules/xbox_controller.py`: Low-level controller input.
- `modules/controller_handler.py`: Input-to-action mapping and event publishing.
- `config/controller_handler.yml`: Main YAML configuration for mappings.
- `config/controller.yml`: (If used) Additional controller configuration.

---

## See Also
- `BaseModule.md` for base class features and messaging system details.

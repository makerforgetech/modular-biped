# BusServo Module Documentation

## Overview

Serial bus servos allow for efficient communication and control of multiple servos over a single bus. The `Servo` class provides a high-level interface to manage these servos, including setting positions, speeds, and handling configurations. The hardware interface is now fully backend-agnostic, supporting multiple libraries and simulation.

## Architecture

The bus_servo module now supports multiple backends:

- **Waveshare**: Uses the official Waveshare ST/SC SDKs for hardware control.
- **Rustypot**: Uses the rustypot library for Feetech and compatible servos.
- **Simulation**: A software-only backend for debugging and development, which logs all actions instead of controlling hardware.

You can select the backend in your configuration. All backends implement the same interface, so you can switch between them without changing your code.

All servo configuration (range, start, poses) is now in **degrees** for clarity and cross-backend compatibility.

## Configuration

The configuration file (e.g. `environments/cody.yml`) contains the configuration for each bus servo. The `instances` section defines the servos, their IDs, and their initial positions, all in degrees. The `poses` section defines named poses, also in degrees.

## Getting Started / Calibration

To calibrate the servos, each must have their ID set individually. To achieve this, connect one servo to the driver board and run `modules/actuators/bus_servo/change_id.py`. This script will prompt you to enter the ID for the connected servo, which will then be saved permanently on the servo.

If you have challenges understanding the current ID of the servo, run `modules/actuators/bus_servo/libraries/waveshare/STServo_examples/read_all.py` or `modules/actuators/bus_servo/libraries/waveshare/SCServo_examples/read_all.py` depending on the servo type. This script will read and display the current ID of the connected servo.

Once the ID has been set for all servos, you can use the `Servo` class to control them by enabling it in the environment yaml file.

### Centering
The servos raw value range is between 0-4095 for ST servos and 0-1024 for SC servos, this equates to 360 and 300 degrees respectively. The position readout can wrap around, so the servos should be set to the midpoint before mounting them in the robot otherwise it can result in the servo passing the wrong way through the range of values, which could damage the robot.  

The `change_id.py` script will set the servo to the midpoint when changing the ID. The servo should then be mounted in the robot at roughly the midpoint position.

You can also enable `center_on_boot` for each servo in the configuration file, which will move the servo to the center of its range on initialization.


### Calibration
To calibrate the servo positions, set the flag `calibrate_on_boot` to `true` in the configuration file for each instance (servo). This will cause the servo to output it's current position in the debug log, which can then be copied into the start position, or range. Servos can be manually moved to any position to identify their range or certain poses. 

Finally, set `calibrate_on_boot` to false and re-run the program to start using the servos with their configured positions.

### Demonstration

To demonstrate the servo movement on boot, set the flag `demonstrate_on_boot` to `true` in the configuration file for each instance (servo). This will cause the servo to move to its minimum and maximum positions once on initialization, allowing you to see the range of motion.

## Subscriptions and direct command

The `Servo` class subscribes to the following topics:
`servo:<identifier>:mv` - to move the servo to a specific position relative to it's current position.
`servo:<identifier>:mvabs` - to move the servo to a specific position with absolute values.

The environment configuration can also inject the servos into a module for direct control:

```
my_module:
  enabled: true
  inject:
    servos: "Servo_*"
```

You can then directly call the servo such as:

```
self.servos['neck_tilt'].move_relative(pitch)
self.servos['neck_tilt'].move(pitch)
```

## Smooth initialization

Because the `Servo` class gets the current position of the servo on initialization, there is no danger of a servo jumping from an unknown position to the start position. This is especially useful when the servos are powered on in a random position and is an advantage over hobby servos.

## SC vs ST servos

The `Servo` class supports both ST and SC series servos from Waveshare, Feetech and compatible servos. The type of servo is determined by the `model` variable in the configuration file, and the backend is selected via the `backend` parameter. The class will automatically use the appropriate backend for the specified servo type.

There are some limitations to the SC servos as they do not support continuous rotation and have a lower rotational range compared to the ST servos. The simulation backend is useful for development and debugging without hardware.

## Backends

- **WaveshareBusServo**: Uses the official Waveshare SDKs for ST/SC servos (this library is included in this repo).
- **RustypotBusServo**: Uses the rustypot library for Feetech and compatible servos (this library is referenced via python import).
- **SimulationBusServo**: Simulates servo behavior and logs all actions for debugging (no library required).

All backends implement the same methods, including movement, speed, torque, calibration, and error handling.

## Notes during testing

- Speed: between 0 and 3000 for SC servos tested, 0 is max, then 1-3000 increases speed.
- Acceleration: between 0 and 3000 for SC servos tested, 0 is max but no significant difference observed between values.
- Overload error occurring fairly frequently on SC servos using Waveshare library. However when testing with scheduled movements the issue is far less frequent. This may be due to sending commands too quickly in succession. Cycling torque off/on seems to resolve the error, otherwise you need to power cycle the servo.
- To disable torque on SC servos use: `self.packetHandler.write1ByteTxRx(self.portHandler, self.index, ADDR_TORQUE_ENABLE, 0)`, change the 0 to 1 to enable torque.
- In some cases the overload error does seem to be caused by load on the servo, in which case toggling the torque does not resolve this. The neck pan is an example of this where the SC servo needed to be replaced with the more powerful ST servo.

## References
https://www.waveshare.com/wiki/ST3215_Servo
https://www.waveshare.com/wiki/SC09_Servo
https://www.waveshare.com/wiki/Bus_Servo_Adapter_(A)
https://github.com/pollen-robotics/rustypot
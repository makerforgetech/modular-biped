# BusServo Module Documentation

## Overview

Serial bus servos allow for efficient communication and control of multiple servos over a single bus. The `Servo` class provides an interface to manage these servos, including setting positions, speeds, and handling configurations.

## Configuration

The `config/servo_bus.yml` file contains the configuration for each bus servo. The `instances` section defines the servos, their IDs, and their initial positions. The `poses` section within each instance defines various poses that can be used to set servo positions.

## Getting Started / Calibration

To calibrate the servos, each must have their ID set individually. To achieve this, connect one servo to the driver board and run `modules/actuators/bus_servo/change_id.py`. This script will prompt you to enter the ID for the connected servo, which will then be saved permanently on the servo.

If you have challenges understanding the current ID of the servo, run `modules/actuators/bus_servo/STServo_examples/read_all.py` or `modules/actuators/bus_servo/SCServo_examples/read_all.py` depending on the servo type. This script will read and display the current ID of the connected servo.

Note: if there is an issue with dependencies, you may need to run the script from within the `modules/actuators/bus_servo` directory.

Once the ID has been set for all servos, you can use the `Servo` class to control them by enabling it in the above yaml file.

### Centering
The servos range is between 0-4095 for ST servos and 0-1024 for SC servos. The position readout can wrap around (from 0 to 4095), so the servos should be set to the midpoint before mounting them in the robot otherwise it can result in the servo passing the wrong way through the range of values, which could damage the robot. 

The `change_id.py` script will set the servo to the midpoint when changing the ID. The servo should then be mounted in the robot at roughly the midpoint position.

You can also enable `center_on_boot` for each servo in the configuration file, which will move the servo to the center of its range on initialization.


### Calibration
To calibrate the servo positions, set the flag `calibrate_on_boot` to `true` in the configuration file for each instance (servo). This will cause the servo to output it's current position in the debug log, which can then be copied into the start position, or range. Servos can be manually moved to any position to identify their range or certain poses.

Note: `calibrate_on_boot` is enabled by default to help with initial configuration.

Once the start position and range are set, move the flag to the next servo and repeat the process until all servos are calibrated.

You can then copy the output values directly from the log into the configuration file.

Finally, set `calibrate_on_boot` to false and re-run the program to start using the servos with their configured positions.

### Demonstration

To demonstrate the servo movement on boot, set the flag `demonstrate_on_boot` to `true` in the configuration file for each instance (servo). This will cause the servo to move to its minimum and maximum positions once on initialization, allowing you to see the range of motion.

## Subscriptions

The `Servo` class subscribes to the following topics:
`servo:<identifier>:mv` - to move the servo to a specific position relative to it's current position.
`servo:<identifier>:mvabs` - to move the servo to a specific position with absolute values.

## Smooth initialization

Because the `Servo` class gets the current position of the servo on initialization, there is no danger of a servo jumping from an unknown position to the start position. This is especially useful when the servos are powered on in a random position and is an advantage over hobby servos used in previous versions of the modular biped.

## SC vs ST servos

The `Servo` class supports both ST and SC series servos from Waveshare and compatible servos. The type of servo is determined by the `model` variable in the configuration file. The class will automatically use the appropriate SDK for the specified servo type.

There are some limitations to the SC servos as they do not support continuous rotation and have a lower rotational range compared to the ST servos. 

## Notes during testing

- Speed: between 0 and 3000 for SC servos tested, 0 is max, then 1-3000 increases speed.
- Acceleration: between 0 and 3000 for SC servos tested, 0 is max but no significant difference observed between values.
- Overload error occurring fairly frequently on SC servos. However when testing with scheduled movements the issue is far less frequent. This may be due to sending commands too quickly in succession. Cycling torque off/on seems to resolve the error, otherwise you need to power cycle the servo.
- To disable torque on SC servos use: `self.packetHandler.write1ByteTxRx(self.portHandler, self.index, ADDR_TORQUE_ENABLE, 0)`, change the 0 to 1 to enable torque.
- One of the SC servos definitely seems more prone to overload errors than the others. It may be a faulty servo. This servo also doesn't always respect speed settings. It can be set to 3000 and move quickly on one movement then slow the next without a change in speed being commanded. This issue may be directional, as both the original SC servos show this behaviour in one direction only.
- In some cases the overload error does seem to be caused by load on the servo, in which case toggling the torque does not resolve this. The neck pan is an example of this where the SC servo needed to be replaced with the more powerful ST servo.

## References
https://www.waveshare.com/wiki/ST3215_Servo
https://www.waveshare.com/wiki/SC09_Servo
https://www.waveshare.com/wiki/Bus_Servo_Adapter_(A)
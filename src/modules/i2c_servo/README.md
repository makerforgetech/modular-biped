# I2CServo Module Documentation

## Overview

The `I2CServo` module is designed to interface with servo motors using the I2C protocol. It provides functionalities to initialize the servos, perform tests, and move the servos to specified angles. This documentation outlines the setup and usage of the `I2CServo` class.

## Configuration

Before using the `I2CServo` module, you need to configure it in the `config/i2c_servo.yml` file. Below is an explanation of the configuration options:

```yaml
i2c_servo:
  enabled: false  # Set to true to enable the I2CServo module
  path: modules.i2c_servo.I2CServo  # Path to the I2CServo class
  config:
    test_on_boot: false  # Set to true to run a test on boot
    servo_count: 16  # Number of servos connected
  dependencies:
    unix:
      - python3-smbus
    python:
      - adafruit-circuitpython-servokit
```

### Dependencies

After enabling the module, run `./install.sh` to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

## Usage

### Initializing the I2CServo

When the module is enabled in the config YAML, the `I2CServo` class is automatically imported and initialized.

You can also reference the `I2CServo` class directly in the `main.py`:

```python
module = module_instances['i2c_servo']  # Get the I2CServo module instance
module.test()  # Run a test on the servos
```

### Testing the Servos

If `test_on_boot` is set to `true` in the configuration, the servos will automatically run a test upon initialization. You can also manually call the `test` method:

```python
i2c_servo.test()
```

### Moving the Servos

The `I2CServo` class provides a method to move the servos to specified angles. Here’s an example of how to move a servo:

```python
i2c_servo.moveServo(index=0, angle=90)  # Move servo at index 0 to 90 degrees
```

## Conclusion

The `I2CServo` module provides a straightforward interface for working with servo motors using the I2C protocol in Python. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and utilize the servo motors in your projects.
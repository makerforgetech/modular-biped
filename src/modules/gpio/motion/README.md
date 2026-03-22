# Sensor Module Documentation

## Overview

The `Sensor` module is designed to interface with a motion sensor using the `gpiozero` library. It provides functionalities to initialize the sensor, read sensor data, and publish motion detection events. This documentation outlines the setup and usage of the `Sensor` class.

## Configuration

Before using the `Sensor` module, you need to configure it in the `config/sensor.yml` file. Below is an explanation of the configuration options:

```yaml
sensor:
  enabled: false  # Set to true to enable the Sensor module
  path: modules.sensor.Sensor  # Path to the Sensor class
  config:
    pin: 4  # GPIO pin number connected to the sensor
    test_on_boot: false  # Set to true to run a test on boot
  dependencies:
    unix:
      - python3-gpiozero
    python:
      - gpiozero
```

### Dependencies

After enabling the module, run `./install.sh` to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

## Usage

### Initializing the Sensor

When the module is enabled in the config YAML, the `Sensor` class is automatically imported and initialized.

You can also reference the `Sensor` class directly in the `main.py`:

```python
module = module_instances['sensor']  # Get the Sensor module instance
module.read()  # Read data from the sensor
```

### Reading Data

The `Sensor` class provides methods to read data from the motion sensor. Here’s an example of how to read data:

```python
def read(self):
    self.value = self.sensor.motion_detected
    return self.value
```

### Publishing Motion Events

The `Sensor` class can publish motion detection events to the application via a pub/sub mechanism. Here’s an example of how to publish a motion event:

```python
def loop(self):
    if self.read():
        self.publish('motion')
```

### Testing the Sensor

The `Sensor` class includes a test method to continuously read data from the sensor and print the results. Here’s an example of how to test the sensor:

```python
def test(self):
    while True:
        print(self.read())
        sleep(1)
```

## Conclusion

The `Sensor` module provides a straightforward interface for working with motion sensors in Python. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and utilize the motion sensor in your projects.
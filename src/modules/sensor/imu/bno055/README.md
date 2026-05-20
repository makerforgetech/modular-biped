# BNO055 Module Documentation

## Overview

The `BNO055` module interfaces with the BNO055 9-DOF sensor using the I2C protocol. It provides initialization, data reading (Euler angles, acceleration, gyroscope, etc.), and publishes sensor data via the pubsub system. This documentation outlines setup and usage of the `BNO055` class.

## Configuration

Configure the module in `config/bno055.yml`:

```yaml
bno055:
  enabled: true
  path: modules.sensor.imu.bno055.BNO055
  instances:
    - name: "imu_head"
      test_on_boot: false
      bus: 1
      address: 0x28 # Default
    - name: "imu_body"
      test_on_boot: false
      bus: 1
      line_offset: 1 # For debugging second sensor on same bus, to display both at the same time
      address: 0x29 # Alternative address if second sensor is used
  dependencies:
    python:
      - adafruit-circuitpython-bno055
      - adafruit-blinka
```

### Dependencies

After enabling, run `./install.sh` to install dependencies. Ensure `adafruit-circuitpython-bno055` and `adafruit-blinka` are installed.

## Usage

### Initializing the BNO055

When enabled in the config YAML, the `BNO055` class is automatically imported and initialized.


You can also reference the `BNO055` class directly in your code:

```python
module = module_instances['imu_head']  # Get the BNO055 module instance
module.read_data()  # Print sensor data to console
euler = module.get_euler()  # Get Euler angles as a tuple
```

### Reading and Publishing Data

- `read_data()`: Prints all sensor values (temperature, acceleration, gyro, euler angles, etc.) to the console.
- `get_euler()`: Returns the Euler angles as a tuple.
- `publish_changed_data()`: Publishes sensor data to the pubsub topic `imu/<name>/data` when significant changes are detected. This is only called if you invoke it manually or if `test_on_boot` is set to `true` in the config (which causes continuous reading/publishing on boot).

### Example Data Output

```python
{
  'temperature': 19,
  'acceleration': (0.17, -9.74, -0.99),
  'magnetic': (12.19, 63.75, 32.25),
  'gyro': (0.001, 0.002, -0.002),
  'euler': (359.94, 0.94, 95.75),
  'quaternion': (0.67, -0.74, -0.01, 0.0),
  'linear_acceleration': (0.01, 0.02, 0.03),
  'gravity': (0.16, -9.75, -0.98)
}
```


## Notes

- The module inherits from `BaseModule` and uses the pubsub system for messaging.
- The `test_on_boot` option will continuously read and print data on startup if set to `true`.
- Data is only published when significant changes are detected to reduce message flooding.
- The module does not automatically subscribe to a loop topic for periodic publishing; you must call `publish_changed_data()` yourself if you want regular updates.

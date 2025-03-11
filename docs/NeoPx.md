# NeoPx Module Documentation

## Overview

The `NeoPx` module is designed to control NeoPixel LEDs using different protocols such as GPIO, I2C, and SPI. This documentation outlines the setup and usage of the `NeoPx` class, including protocol compatibility with various Raspberry Pi versions.

## Configuration

Before using the `NeoPx` module, you need to configure it in the `config/neopx.yml` file. Below is an explanation of the configuration options:

```yaml
neopx:
  enabled: false  # Set to true to enable the NeoPx module
  path: modules.neopixel.neopx.NeoPx  # Path to the NeoPx class
  config:
    pin: 12 # Only used for GPIO. GPIO2 and 3 are use for i2c, GPIO10 is used for SPI, GPIO12 is used for GPIO
    protocol: 'SPI' # choose between GPIO, I2C and SPI (see below)
    count: 12
```

### Dependencies

After enabling the module, run `./install.sh` to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

## Protocol Compatibility

### GPIO

- **Not supported on Raspberry Pi 5**.
- Suitable for older Raspberry Pi versions.

### I2C

- Supported on the 'buddy' release.
- Requires the `adafruit-circuitpython-seesaw` library.

### SPI

- Supported on the 'Cody' release.
- Requires the `neopixel_spi` library.

## Usage

### Initializing the NeoPx

When the module is enabled in the config YAML, the `NeoPx` class is automatically imported and initialized.

You can also reference the `NeoPx` class directly in the main.py:

```python
module = module_instances['neopx']  # Get the NeoPx module instance
module.set(module.all, NeoPx.COLOR_RED)  # Set all pixels to red
```

### Setting Pixel Colors

The `NeoPx` class provides methods to set the color of individual or multiple pixels. Here’s an example of how to set the color of a pixel:



```python
# Using messaging
self.publish('led', identifiers=[0], color='red')

# Directly accessing the module (see above)
module.set(1, 'red')  # Set pixel 1 to red
module.set([0, 2, 4], (0, 255, 0))  # Set pixels 0, 2, and 4 to green
```

### Flashlight Mode

To turn on or off all pixels in flashlight mode:

```python
# Using messaging
self.publish('led/flashlight', state=True)  # Turn on flashlight mode
self.publish('led/flashlight', state=False)  # Turn off flashlight mode

# Directly accessing the module (see above)
module.flashlight(True)  # Turn on flashlight mode
module.flashlight(False)  # Turn off flashlight mode
```

## Conclusion

The `NeoPx` module provides a flexible interface for controlling NeoPixel LEDs using different protocols. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and utilize NeoPixels in your projects.

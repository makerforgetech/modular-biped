# TFTDisplay Module Documentation

## Overview

The `TFTDisplay` module is designed to interface with a TFT display using the SPI protocol. It provides functionalities to initialize the display, perform tests, and draw graphics on the screen. This documentation outlines the setup and usage of the `TFTDisplay` class.

## Configuration

Before using the `TFTDisplay` module, you need to configure it in the `config/tft_display.yml` file. Below is an explanation of the configuration options:

```yaml
tft_display:
  enabled: false  # Set to true to enable the TFTDisplay module
  path: modules.display.tft_display.TFTDisplay  # Path to the TFTDisplay class
  config:
    bus: 0  # SPI bus number (0 for /dev/spidev0.0)
    device: 0  # SPI device number (0 for /dev/spidev0.0)
    rst_pin: 27  # GPIO pin for reset
    dc_pin: 25  # GPIO pin for data/command
    bl_pin: 18  # GPIO pin for backlight (not used if no backlight)
    test_on_boot: true  # Set to true to run a test on boot
  dependencies:
    unix:
      - python3-pip
      - python3-pil
      - python3-numpy
    python:
      - spidev
```

### Dependencies

After enabling the module, run ./install.sh to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

This module utilises the waveshare library. More information available here: https://www.waveshare.com/wiki/2.4inch_LCD_Module#Python

## Usage

### Display size

There are multiple libraries available for working with TFT displays. The `TFTDisplay` module uses the `ST7735` library, which supports a resolution of 240x240 pixels.

The import and initialization of the display must be adjusted for other devices.

```python
from modules.display.lib import LCD_1inch28
self.disp = LCD_1inch28.LCD_1inch28(spi=spi, spi_freq=10000000, rst=kwargs.get('rst_pin'), dc=kwargs.get('dc_pin') , bl=kwargs.get('bl_pin'))
```

This is not currently supported via the config YAML, but could be added in the future.

### Initializing the TFTDisplay

When the module is enabled in the config YAML, the `TFTDisplay` class is automatically imported and initialized.

You can also reference the `TFTDisplay` class directly in the main.py:

```python
module = module_instances['tft_display'] # Get the TFTDisplay module instance
module.test_display()  # Run a test on the display
```

### Testing the Display

If `test_on_boot` is set to `true` in the configuration, the display will automatically run a test upon initialization. You can also manually call the `test_display` method:

```python
tft_display.test_display()
```

### Drawing on the Display

The `TFTDisplay` class provides methods to draw shapes and images on the display. Here’s an example of how to draw an arc and lines:

```python
from PIL import Image, ImageDraw

# Create a blank image
image = Image.new("RGB", (tft_display.disp.width, tft_display.disp.height), "BLACK")
draw = ImageDraw.Draw(image)

# Draw an arc
draw.arc((1, 1, 239, 239), 0, 360, fill=(0, 0, 255))

# Draw lines
draw.line([(120, 1), (120, 12)], fill=(128, 255, 128), width=4)

# Display the image
tft_display.disp.ShowImage(image)
```

### Clearing the Display

To clear the display, you can call the `clear` method:

```python
tft_display.disp.clear()
```

### Setting the Backlight

You can adjust the backlight brightness using the `bl_DutyCycle` method:

```python
tft_display.disp.bl_DutyCycle(50)  # Set backlight to 50%
```

## Conclusion

The `TFTDisplay` module provides a straightforward interface for working with TFT displays in Python. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and utilize the TFT display in your projects.
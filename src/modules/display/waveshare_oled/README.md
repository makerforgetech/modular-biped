# WaveshareOLED

## Overview

Waveshare OLED display driver module.

## Configuration

Configuration is defined in `config.yml` within this directory:

```yaml
oled_display:
  enabled: false  # Set to true to enable this module
  path: modules.display.waveshare_oled.waveshare_oled.WaveshareOLED
  config:
    # See config.yml for available options
```

## Usage

Enable the module in `config.yml` and it will be automatically loaded by the `ModuleLoader`.

## Testing

Run the module tests with:
```bash
python3 -m unittest discover -s modules -p 'test_*.py'
```

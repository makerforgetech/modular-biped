# Read

## Overview

General purpose GPIO input reader module.

## Configuration

Configuration is defined in `config.yml` within this directory:

```yaml
gpio_read:
  enabled: false  # Set to true to enable this module
  path: modules.gpio.read.read.Read
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

# ArduinoSerial

## Overview

Arduino serial communication module using robust-serial protocol.

Communicate with Arduino over Serial

## Configuration

Configuration is defined in `config.yml` within this directory:

```yaml
serial:
  enabled: false  # Set to true to enable this module
  path: modules.network.arduinoserial.arduinoserial.ArduinoSerial
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

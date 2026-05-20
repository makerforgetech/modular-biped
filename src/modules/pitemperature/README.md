# PiTemperature

## Overview

Monitors Raspberry Pi CPU temperature and throttles/sleeps the system when needed.

## Configuration

Configuration is defined in `config.yml` within this directory:

```yaml
pitemperature:
  enabled: false  # Set to true to enable this module
  path: modules.pitemperature.pitemperature.PiTemperature
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

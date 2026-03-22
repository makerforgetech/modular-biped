# ControllerHandler

## Overview

Maps controller inputs to robot actions based on configurable mappings.

Consume controller input and map to messaging events.

Requires injection of a controller module that provides input data.

## Configuration

Configuration is defined in `config.yml` within this directory:

```yaml
controller:
  enabled: false  # Set to true to enable this module
  path: modules.controller_handler.controller_handler.ControllerHandler
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

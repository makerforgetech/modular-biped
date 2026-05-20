# Vision

## Overview

IMX500 AI camera vision module for object detection.

## Configuration

Configuration is defined in `config.yml` within this directory:

```yaml
vision_imx500:
  enabled: false  # Set to true to enable this module
  path: modules.vision.imx500.vision.vision.Vision
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

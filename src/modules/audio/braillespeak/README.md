# BrailleSpeak

## Overview

Braille-based speech output module.

Communicate with tones, letters converted to tone pairs
Uses Buzzer module to play tones via pubsub

:param kwargs: pin, duration

Subscribes to 'speak' event

Example:
self.publish('speak', msg="Hi")

## Configuration

Configuration is defined in `config.yml` within this directory:

```yaml
braillespeak:
  enabled: false  # Set to true to enable this module
  path: modules.audio.braillespeak.braillespeak.BrailleSpeak
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

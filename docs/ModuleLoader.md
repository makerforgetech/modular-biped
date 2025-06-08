# ModuleLoader Documentation

## Overview

The `ModuleLoader` class is responsible for dynamically loading and instantiating modules based on YAML configuration files. It supports both base (version-controlled) configuration and local instance-specific overrides, enabling flexible and environment-specific setups without modifying the main configuration files.

## Key Features

1. **Dynamic Module Loading**: Loads Python modules and creates instances based on configuration.
2. **YAML-Based Configuration**: Reads module definitions from YAML files in the `config/` directory.
3. **Local Overrides**: Supports local override YAML files (e.g., `config/overrides/*.local.yml`) to customize module settings per instance.
4. **Messaging Service Integration**: Can inject a messaging service into loaded modules.
5. **Multiple Instances**: Supports loading multiple instances of a module with different configurations.

## How ModuleLoader Works

- Scans the `config/` directory for `.yml` files describing modules.
- For each module, checks for a corresponding local override file in `config/overrides/` (e.g., `vision_imx500.local.yml`).
- Merges the local override into the base configuration, with the override taking precedence.
- Dynamically imports the specified Python class and instantiates it with the merged configuration.
- Returns a dictionary of module instances for use in your application.

## Example: Base and Local Override YAML

### Base Configuration (`config/vision_imx500.yml`)

```yaml
vision_imx500:
  enabled: true
  path: modules.vision.imx500.vision.Vision
  config:
    preview: false
    pin: 17
```

### Local Override (`config/overrides/vision_imx500.local.yml`)

```yaml
vision_imx500:
  enabled: false
  config:
    preview: true
    pin: 22
```

> **Note:** Local override files have been added to `.gitignore` to avoid committing instance-specific settings. They have also been excluded from mutagen sync.

## How to Use ModuleLoader

### Loading Modules

```python
# filepath: /home/dan/projects/modular-biped/main.py
from module_loader import ModuleLoader

loader = ModuleLoader()
modules = loader.load_modules()

# Access a loaded module instance
vision = modules['Vision']
```

### Setting the Messaging Service

```python
# filepath: /home/dan/projects/modular-biped/main.py
messaging_service = ...  # Your messaging service instance
loader.set_messaging_service(modules, messaging_service)
```

## Creating Local Override YAML Files

1. **Create an override file** in `config/overrides/` with the same base name as the module config, but with `.local.yml` extension.
2. **Specify only the keys you want to override** (e.g., `enabled`, `config` values).
3. **Do not commit override files** to version control.

**Example Directory Structure:**
```
config/
  vision_imx500.yml
  ...
  overrides/
    vision_imx500.local.yml
.gitignore
```

**Example `.gitignore` Entry:**
```
config/overrides/*.local.yml
```

## Deep Merge Behavior

When both base and override YAML files are present, the loader recursively merges the override into the base. This means only the specified keys in the override file will replace or extend the base configuration.

**Example Merge Result:**

Base:
```yaml
config:
  preview: false
  pin: 17
  foo: bar
```
Override:
```yaml
config:
  preview: true
```
Result:
```yaml
config:
  preview: true
  pin: 17
  foo: bar
```

## Conclusion

The `ModuleLoader` class provides a robust and flexible way to manage module configuration and instantiation in your project. By leveraging local override YAML files, you can easily customize behavior for different environments or hardware setups without modifying the main configuration files or risking merge conflicts in version control.

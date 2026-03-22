# ModuleLoader Documentation

## Overview

The `ModuleLoader` class (`src/module_loader.py`) is responsible for dynamically loading and instantiating modules in the project based on YAML configuration files. It uses per-environment YAML files to determine which modules are enabled and how they are configured and wired together.

## Key Features

1. **Dynamic Module Loading**: Loads Python modules and classes at runtime, inferring the Python file path from the `config.yml` directory location.
2. **Environment-based Configuration**: Loads `environments/<environment>.yml` to determine which modules are enabled and provides device-specific configuration overrides.
3. **Config Merging**: Device-specific `config:` values shallow-merge over module defaults; device-specific `instances:` replaces the module's instance list.
4. **Config-driven Dependency Injection**: `inject_dependencies()` reads `inject:` / `on_inject:` blocks from the environment YAML and automatically wires modules together — no manual wiring in `main.py`.
5. **Messaging Service Integration**: Automatically injects the messaging service into all loaded modules.

## Directory Structure

```
environments/          # Per-device environment YAML files
  archie.yml
  buddy.yml
  cody.yml
  server.yml
  laptop.yml

src/
  module_loader.py     # ModuleLoader implementation
  main.py
  system_loop.py
  modules/             # All module source code
    <module>/
      <module>.py      # Python implementation (filename matches directory)
      config.yml       # Module class + generic defaults
      README.md        # Documentation
      tests/           # Unit tests
```

## Environment File Format

```yaml
# environments/archie.yml
messaging_service:
  enabled: true

personality:
  enabled: true
  inject:
    servos: "Servo_*"          # wildcard → {servo.identifier: servo} dict
    imu.head: BNO055_imu_head  # dotted path → target.imu['head'] = instance
    imu.body: BNO055_imu_body
    vision: Vision

controller_handler:
  enabled: true
  inject:
    controller: XboxController
  on_inject:
    - start                    # called after all injections

bus_servo:
  enabled: true
  config:
    # device-specific overrides merged over module defaults
  instances:
    - name: neck_pan
      id: 12
      range: [0, 3412]
```

## Usage

```python
from module_loader import ModuleLoader

loader = ModuleLoader(config_folder="modules", environment="laptop")
module_instances = loader.load_modules()
loader.inject_dependencies(module_instances)
```

## inject_dependencies Injection Syntax

| Syntax | Effect |
|--------|--------|
| `attr: InstanceKey` | `target.attr = instances['InstanceKey']` |
| `attr.sub: InstanceKey` | `target.attr['sub'] = instances['InstanceKey']` |
| `attr: "Prefix_*"` | `target.attr = {inst.identifier: inst for all matching}` |
| `on_inject: [method]` | calls `target.method()` after all injections |

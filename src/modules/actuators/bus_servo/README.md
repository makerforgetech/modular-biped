# BusServo Module Documentation

## Overview

Serial bus servos allow for efficient communication and control of multiple servos over a single bus. The `ServoManager` class provides a centralised, high-level interface to manage all servos on a bus, including setting positions, coordinating multi-servo motions, and handling configuration. The hardware interface is backend-agnostic, supporting multiple libraries and simulation.

## Architecture

### ServoManager

`ServoManager` is the single `BaseModule` responsible for all bus servo operations:

- Owns one shared hardware controller per physical serial bus (port + baudrate).  Multiple servos on the same bus open the port **only once**, avoiding contention.
- Maintains a registry of lightweight `ServoState` objects keyed by servo name.
- Handles all messaging subscriptions for every managed servo.
- Processes per-servo move queues each system-loop cycle.
- Provides high-level APIs for coordinated motion: `move_to_pose()`, `group_move()`.

### ServoState

`ServoState` is a lightweight per-servo holder:

- Stores only configuration and logical state: name, ID, model, range, speed, acceleration, current position, move queue, and poses.
- Does **not** own the serial port or controller.
- Delegates every hardware operation (move, read position, torque enable/disable) to the owning `ServoManager`.

### Backends

| Backend | Class | Notes |
|---------|-------|-------|
| `waveshare` | `WaveshareBusServo` | Official Waveshare ST/SC SDKs (included). Port shared via class-level singleton. |
| `rustypot` | `RustypotBusServo` | Rustypot library for Feetech-compatible servos. |
| `simulation` | `SimulationBusServo` | Software-only, logs all actions; no hardware required. |

All backends implement the same `BusServoBase` interface.

## Configuration

Servos are declared in the environment YAML file (e.g. `environments/cody.yml`) under a single `bus_servo` entry.  All servo instances are listed under `config.servos`; the `ServoManager` is instantiated **once** and manages all of them.

```yaml
bus_servo:
  enabled: true
  config:
    backend: 'waveshare'   # waveshare | rustypot | simulation
    poses:
      - stand: {leg_r_tilt: 246.7, leg_l_tilt: 142.6, ...}
    servos:
      - name: leg_r_tilt
        model: ST3215
        id: 1
        range: [220.9, 346.6]
        start: 246.9
      - name: neck_tilt
        model: SC09
        baudrate: 115200   # overrides the default baudrate for this servo
        id: 11
        range: [8.8, 64.5]
        start: 35.2
        speed: 60
```

## Injecting into other modules

Inject the `ServoManager` into modules that need direct servo access:

```yaml
my_module:
  enabled: true
  inject:
    servos: ServoManager
```

Because `ServoManager` exposes a dict-like interface, existing code that accesses servos via `self.servos[name]` continues to work unchanged:

```python
self.servos['neck_tilt'].move_relative(pitch)
self.servos['neck_pan'].move(150)
for name, servo in self.servos.items():
    servo.detach()
```

## Messaging

The manager subscribes automatically for every servo listed in `config.servos`:

| Topic | Action |
|-------|--------|
| `servo:<name>:mvabs` | Queue absolute move (degrees) |
| `servo:<name>:mv` | Queue relative move (delta degrees) |
| `servo:<name>:queue` | Alias for absolute move |
| `servo/pose` | Move all servos to a named pose |

## Coordinated motion

Use `group_move()` to queue moves for multiple servos in one call:

```python
self.servo_manager.group_move({
    'leg_l_hip': 180,
    'leg_r_hip': 180,
    'leg_l_knee': 90,
    'leg_r_knee': 90,
})
```

Or publish a named pose to move all servos simultaneously:

```python
self.publish('servo/pose', pose_name='stand_low')
```

## Getting Started / Calibration

To calibrate the servos, each must have their ID set individually. Connect one servo to the driver board and run `modules/actuators/bus_servo/change_id.py`. This script will prompt you to enter the ID for the connected servo.

If you need to discover a servo's current ID, run `modules/actuators/bus_servo/libraries/waveshare/STServo_examples/read_all.py` (ST) or the SC equivalent.

### Centering

Servo raw values range from 0–4095 (ST, 360°) or 0–1024 (SC, 300°). Set servos to their midpoint before mounting to avoid wrapping through the wrong direction.

### Calibration via `calibrate_on_boot`

Set `calibrate_on_boot: true` for a servo in the config to continuously log its current position. Move the servo manually, then copy min/max values into `range`.  Disable the flag when done.

### Demonstration

Set `demonstrate_on_boot: true` to sweep a servo through its full range on startup.

## SC vs ST servos

Both families are supported via the same backend; the `model` field selects the correct SDK.  ST servos (e.g. ST3215) have 360° range and support continuous-rotation mode.  SC servos (e.g. SC09) have a 300° range.

## Notes

- Speed: 0 = max on SC servos; 1–3000 slows it down.
- Overload errors on SC servos can sometimes be resolved by toggling torque off/on.

## References

- https://www.waveshare.com/wiki/ST3215_Servo
- https://www.waveshare.com/wiki/SC09_Servo
- https://www.waveshare.com/wiki/Bus_Servo_Adapter_(A)
- https://github.com/pollen-robotics/rustypot

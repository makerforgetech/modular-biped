# SystemLoop Module Documentation

## Overview

The `SystemLoop` class manages the main event loop for the robot, controlling periodic actions and system state transitions. It is responsible for publishing loop events, handling sleep/throttle modes, and responding to system-wide signals. This documentation explains its operation, configuration, and state management.

## States and Behavior

The loop operates in three primary states:

### 1. Normal Running
- **State:** `STATE_RUNNING`
- **Sleep Interval:** 0.01 seconds (10ms) - This is to avoid 100% CPU usage.
- **Behavior:**
  - Publishes periodic events:
    - `system/loop` (every cycle)
    - `system/loop/1` (every second)
    - `system/loop/10` (every 10 seconds)
    - `system/loop/60` (every 60 seconds)
  - Used for real-time control and frequent updates.

### 2. Throttled Running
- **State:** `STATE_THROTTLED`
- **Sleep Interval:** 1 second
- **Behavior:**
  - Publishes the same periodic events as normal running, but at a much slower rate.
  - Used to reduce CPU usage, typically triggered by high temperature or other system constraints.
  - Can be entered via the `system/throttle` topic.

### 3. Sleep Mode
- **State:** `STATE_SLEEPING`
- **Sleep Interval:** (as set, but loop events are skipped)
- **Behavior:**
  - Does **not** publish any loop events (`system/loop`, `system/loop/1`, etc.).
  - The loop continues running, but only listens for state-changing topics.
  - Can be entered via the `system/sleep` topic and exited via `system/wake` or other triggers.
  - Typically triggered during extremely high temperature or when the gpio/motion module indicates no motion for a set period.

## State Transitions

- **To Throttled:**
  - Triggered by publishing to `system/throttle` (e.g., high temperature).
  - Increases sleep interval to 1 second.
- **To Sleep:**
  - Triggered by publishing to `system/sleep` (e.g., inactivity, motion timeout).
  - Stops publishing loop events.
- **To Running:**
  - Triggered by publishing to `system/wake`.
  - Resumes normal loop event publishing and resets sleep interval to 0.01 seconds.

## Event Publishing

The following events are published by the loop:
- `system/loop` — every cycle (when running or throttled)
- `system/loop/1` — every second
- `system/loop/10` — every 10 seconds
- `system/loop/60` — every 60 seconds
- `log` — periodic status updates and state changes

## Topic Subscriptions

`SystemLoop` subscribes to:
- `system/sleep` — enters sleep mode
- `system/wake` — exits sleep mode
- `system/throttle` — enters throttled mode
- `gpio/motion` — updates motion state and can trigger sleep/wake transitions

## Motion Handling

The loop listens to the `gpio/motion` topic to determine the last detected motion time. If no motion is detected for a specified duration (e.g., 30 seconds), the loop can transition to sleep mode to conserve resources.

Even in sleep mode, the module can wake up upon receiving motion updates or explicit wake commands.

## Example Usage

Typically called from main.py:

```python
from system_loop import SystemLoop
system_loop = SystemLoop(messaging_service)
system_loop.start()
```

## Customization

You can adjust the sleep intervals and add new state transitions by modifying the class constants and event handlers. The loop is designed to be extensible for additional system states or periodic actions.
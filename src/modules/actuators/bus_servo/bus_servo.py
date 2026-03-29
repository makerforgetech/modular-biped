#!/usr/bin/env python

import collections
import sys
import select
import time
from modules.base_module import BaseModule
from modules.actuators.bus_servo.libraries.factory import BusServoFactory


class ServoState:
    """
    Lightweight servo configuration and state holder.

    Stores per-servo identity and logical state (position, queue) only.
    All hardware operations are delegated to the owning ServoManager so
    that a single shared controller instance handles every servo on a bus.
    """

    def __init__(self, manager, **kwargs):
        self._manager = manager
        self.identifier = kwargs.get('name')
        self.model = kwargs.get('model', 'ST')
        self.index = kwargs.get('id')
        self.range = kwargs.get('range')
        self.start = kwargs.get('start')
        self.port = kwargs.get('port', '/dev/ttyAMA0')
        self.baudrate = kwargs.get('baudrate', 1000000)
        self.speed = kwargs.get('speed', 300)
        self.acceleration = kwargs.get('acceleration', 50)
        self.pos = None
        self._move_queue = collections.deque()

        # Accept either a pre-converted poses dict or a list of single-key dicts
        poses = kwargs.get('poses', [])
        if isinstance(poses, dict):
            self.poses = poses
        else:
            self.poses = {list(p.keys())[0]: list(p.values())[0] for p in poses}

    # ------------------------------------------------------------------
    # Queue helpers
    # ------------------------------------------------------------------

    def move(self, position, speed=None, acceleration=None, delay=0, **kwargs):
        """Queue a move to an absolute position (degrees)."""
        self._move_queue.append({
            'position': position,
            'speed': speed if speed is not None else self.speed,
            'acceleration': acceleration if acceleration is not None else self.acceleration,
            'timestamp': time.time(),
            'delay': delay,
        })

    def move_relative(self, delta):
        """Queue a relative move from the current position."""
        if self.pos is None:
            return
        new_position = round(self.pos + delta)
        if self.range:
            if new_position < self.range[0] or new_position > self.range[1]:
                new_position = self.range[0] if new_position < self.range[0] else self.range[1]
        self.move(new_position)

    # ------------------------------------------------------------------
    # Hardware delegates → ServoManager
    # ------------------------------------------------------------------

    def detach(self):
        """Disable torque via the manager."""
        self._manager.detach_servo(self.identifier)

    def attach(self):
        """Enable torque via the manager."""
        self._manager.attach_servo(self.identifier)

    def get_position(self):
        """Return the current hardware position (degrees) via the manager."""
        return self._manager.get_servo_position(self.identifier)

    def is_moving(self):
        """Return True if the servo is still moving (via the manager)."""
        return self._manager.is_servo_moving(self.identifier)

    def calibrate_to_center(self):
        """Move the servo to the centre of its range via the manager."""
        self._manager.calibrate_servo_to_center(self.identifier)


class ServoManager(BaseModule):
    """
    Central manager for all bus servos.

    Owns the shared hardware backend controller(s) and manages every servo
    operation, including coordinated group moves and pose transitions.

    ServoState instances are lightweight holders that delegate all hardware
    access through this manager, ensuring:
      - a single serial port is opened per bus;
      - motion commands can be batched, sequenced, or synchronised;
      - all hardware access is serialised through one place.

    The manager exposes a dict-like interface (``__getitem__``, ``items()``,
    ``values()``, ``get()``) so existing code that treats the injected
    ``servos`` attribute as a ``{name: servo}`` mapping continues to work
    without modification.
    """

    def __init__(self, **kwargs):
        self.backend = kwargs.get('backend', 'waveshare')
        self._default_port = kwargs.get('port', '/dev/ttyAMA0')
        self._default_baudrate = kwargs.get('baudrate', 1000000)
        self._default_speed = kwargs.get('speed', 300)
        self._default_acceleration = kwargs.get('acceleration', 50)

        # Shared poses: {pose_name: {servo_name: position_degrees}}
        poses_list = kwargs.get('poses', [])
        self._poses = {list(p.keys())[0]: list(p.values())[0] for p in poses_list}

        self._servos = {}          # {name: ServoState}
        self._servo_backends = {}  # {name: BusServoBase}

        for servo_cfg in kwargs.get('servos', []):
            # Apply manager-level defaults where the servo config does not
            # supply its own value, then override with servo-specific values.
            full_cfg = {
                'port': self._default_port,
                'baudrate': self._default_baudrate,
                'speed': self._default_speed,
                'acceleration': self._default_acceleration,
                **servo_cfg,
                'poses': self._poses,  # share the global poses dict
            }
            servo_state = ServoState(manager=self, **full_cfg)
            self._servos[servo_state.identifier] = servo_state

            # Create per-servo backend.  Port/controller sharing is handled
            # transparently by class-level singletons inside each backend class.
            backend = BusServoFactory.create(
                backend=self.backend,
                model=servo_state.model,
                servo_id=servo_state.index,
                port=servo_state.port,
                baudrate=servo_state.baudrate,
                range=servo_state.range,
            )
            self._servo_backends[servo_state.identifier] = backend

    # ------------------------------------------------------------------
    # Dict-like interface for backward-compatible injection
    # ------------------------------------------------------------------

    def __getitem__(self, key):
        return self._servos[key]

    def __iter__(self):
        return iter(self._servos)

    def __contains__(self, key):
        return key in self._servos

    def items(self):
        return self._servos.items()

    def values(self):
        return self._servos.values()

    def get(self, key, default=None):
        return self._servos.get(key, default)

    # ------------------------------------------------------------------
    # BaseModule hooks
    # ------------------------------------------------------------------

    def setup_messaging(self):
        """Subscribe to per-servo and global topics for all managed servos."""
        for name, servo in self._servos.items():
            self.subscribe(f'servo:{name}:mvabs', servo.move)
            self.subscribe(f'servo:{name}:mv', servo.move_relative)
            self.subscribe(f'servo:{name}:queue', servo.move)
        self.subscribe('servo/pose', self.move_to_pose)
        self.subscribe('system/exit', self.exit)

        # Initialise positions and queue start moves
        for name, servo in self._servos.items():
            try:
                servo.pos = self.get_servo_position(name)
            except Exception:
                if servo.start is not None:
                    servo.pos = servo.start
                elif servo.range:
                    servo.pos = servo.range[0]
                else:
                    servo.pos = 0
                    self.log(
                        f"No range or start configured for servo {name}; "
                        f"initialising position to 0",
                        level='warning',
                    )
            if servo.start is not None:
                servo.move(servo.start)

    def loop(self):
        """Process every servo's move queue once per system-loop cycle."""
        for servo in self._servos.values():
            self._process_servo_queue(servo)

    # ------------------------------------------------------------------
    # Internal queue processing
    # ------------------------------------------------------------------

    def _process_servo_queue(self, servo):
        """Drain one item from the given servo's queue if the servo is idle."""
        if not servo._move_queue:
            return
        if self.is_servo_moving(servo.identifier):
            return
        next_item = servo._move_queue[0]
        if time.time() - next_item['timestamp'] >= next_item['delay']:
            servo._move_queue.popleft()
            self._do_move(servo, next_item['position'],
                          next_item['speed'], next_item['acceleration'])

    def _do_move(self, servo, position, speed=None, acceleration=None):
        """Execute a single hardware move for the given ServoState."""
        if position is None:
            self.log(f"Position is None for servo {servo.identifier}, cannot move",
                     level='error')
            return
        if servo.range and (position < servo.range[0] or position > servo.range[1]):
            self.log(
                f"Position {position} out of range "
                f"({servo.range[0]}-{servo.range[1]})",
                level='error',
            )
            return
        backend = self._servo_backends.get(servo.identifier)
        if backend is None:
            return
        if speed is not None and hasattr(backend, 'set_speed'):
            backend.set_speed(speed)
        if acceleration is not None and hasattr(backend, 'set_acceleration'):
            backend.set_acceleration(acceleration)
        backend.move_to(position, unit='degrees')
        servo.pos = position

    # ------------------------------------------------------------------
    # High-level coordination APIs
    # ------------------------------------------------------------------

    def move_to_pose(self, pose_name):
        """Queue moves for all servos to the positions defined in the named pose."""
        pose_values = self._poses.get(pose_name, {})
        if not pose_values:
            self.log(f"Pose '{pose_name}' not found", level='warning')
            return
        for servo_name, position in pose_values.items():
            if servo_name in self._servos:
                self._servos[servo_name].move(position)

    def group_move(self, moves):
        """
        Queue coordinated moves for multiple servos.

        :param moves: ``{servo_name: position}`` dict or iterable of
                      ``(servo_name, position)`` pairs.
        """
        if isinstance(moves, dict):
            moves = moves.items()
        for servo_name, position in moves:
            if servo_name in self._servos:
                self._servos[servo_name].move(position)

    # ------------------------------------------------------------------
    # Per-servo hardware delegates
    # ------------------------------------------------------------------

    def get_servo_position(self, servo_name):
        """Return the current hardware position (degrees) of the named servo."""
        backend = self._servo_backends.get(servo_name)
        if backend is None:
            return None
        return backend.get_position(unit='degrees')

    def is_servo_moving(self, servo_name):
        """Return True if the named servo is still moving."""
        servo = self._servos.get(servo_name)
        backend = self._servo_backends.get(servo_name)
        if servo is None or backend is None:
            return False
        try:
            moving = backend.get_moving()
        except Exception as e:
            self.log(f"Exception in get_moving for servo {servo_name}: {e}",
                     level='error')
            return False
        if moving == 1:
            return True
        if servo.pos is not None:
            try:
                pos = self.get_servo_position(servo_name)
                if pos is not None and abs(servo.pos - pos) > 2:
                    self.log(
                        f"Servo {servo_name} not reported as moving but position "
                        f"mismatch: target={servo.pos}, current={pos}",
                        level='warning',
                    )
            except Exception:
                pass
        return False

    def detach_servo(self, servo_name):
        """Disable torque on the named servo."""
        backend = self._servo_backends.get(servo_name)
        if backend:
            backend.detach()

    def attach_servo(self, servo_name):
        """Enable torque on the named servo."""
        backend = self._servo_backends.get(servo_name)
        if backend:
            backend.attach()

    def calibrate_servo_to_center(self, servo_name):
        """Move the named servo to the centre of its configured range."""
        backend = self._servo_backends.get(servo_name)
        if backend:
            backend.calibrate_to_center()

    def detach_all(self):
        """Disable torque on every managed servo."""
        for name in self._servos:
            self.detach_servo(name)

    def exit(self, **kwargs):
        """Disable torque and release all backends on system exit."""
        self.detach_all()
        for backend in self._servo_backends.values():
            try:
                backend.exit()
            except Exception:
                pass



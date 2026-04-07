import time
from random import choice, randint

from modules.base_module import BaseModule


class Companion(BaseModule):
    """
    Companion module — manages Cody's personality, state and multi-modal responses.

    Replaces the monolithic Personality module with a clean state machine and a
    proper AI pipeline so Cody behaves as a helpful, reactive companion robot.

    States
    ------
    sleeping    No motion for ``sleep_timeout`` seconds.  Publishes
                ``system/sleep`` so the system loop throttles hardware.
    idle        Awake but not interacting.  Runs periodic idle animations
                and cycles the display.
    attentive   Person or motion detected.  Tracks the visitor and is ready
                to converse.
    interacting AI pipeline is active (speech heard or message received).

    Subscriptions (inputs)
    ----------------------
    system/loop/1           Second-tick: state management, balance, display.
    system/loop/10          Ten-second tick: periodic housekeeping.
    gpio/motion             Motion sensor — wake from sleep, update attention.
    vision/detections       Person tracking and proactive greeting.
    speech                  Spoken input from SpeechInput module.
    ai/response             AI-generated response from ChatGPT module.
    telegram/received       Inbound Telegram message.
    system/temperature      Pi CPU temperature.
    system/debug/log_hz     Main-loop frequency for display.
    serial                  Serial activity — resets interaction timer.

    Publications (outputs)
    ----------------------
    ai/input                Route text to the ChatGPT module.
    tts                     Speak a message aloud.
    animate                 Trigger a named animation.
    eye/blink               Blink the eye display.
    eye/look                Move the eye display to track a person.
    led                     Set NeoPixel LED colours.
    display/body/text       Update the body OLED/TFT display.
    display/background      Change display background colour.
    system/sleep            Request system sleep (to SystemLoop).
    system/wake             Request system wake (to SystemLoop).
    telegram/respond        Reply to a Telegram user.

    Dependency injection (cody.yml ``inject`` block)
    -------------------------------------------------
    servos      dict of Servo instances (``Servo_*`` wildcard) — used for
                balance and head-tracking servo movements that require the
                ``move_degrees`` API which is not exposed over pubsub.
    imu.head    BNO055 instance for chicken-head stabilisation.
    imu.body    BNO055 instance for balance.
    """

    STATE_SLEEPING = 'sleeping'
    STATE_IDLE = 'idle'
    STATE_ATTENTIVE = 'attentive'
    STATE_INTERACTING = 'interacting'

    # Idle animations played when the robot is bored
    _IDLE_ANIMATIONS = [
        'head_shake',
        'head_nod',
        'head_left',
        'head_right',
        'look_up',
    ]

    # LED colour per state
    _STATE_LED = {
        STATE_SLEEPING: 'dark_gray',
        STATE_ATTENTIVE: 'green',
        STATE_INTERACTING: 'yellow',
    }

    def __init__(self, **kwargs):
        # ── State ────────────────────────────────────────────────────────────
        self.state = self.STATE_IDLE

        # ── Timing ───────────────────────────────────────────────────────────
        self.start_time = time.time()
        self.sleep_timeout = kwargs.get('sleep_timeout', 120)
        self.last_interaction_time = time.time()
        self.last_motion_time = None
        self.last_person_seen_time = None

        # ── Greeting ─────────────────────────────────────────────────────────
        self.greeting_cooldown = kwargs.get('greeting_cooldown', 60)
        self.last_greeting_time = None

        # ── Display ───────────────────────────────────────────────────────────
        self.temperature = None
        self.current_hz = 0
        self.display_state = 0
        self.display_change = time.time()

        # ── LED status strip ─────────────────────────────────────────────────
        self.led_colors = ['off'] * 5
        self.last_led_time = None

        # ── Idle action scheduling ────────────────────────────────────────────
        self.min_interval = kwargs.get('min_interval', 20)
        self.max_interval = kwargs.get('max_interval', 60)
        self.next_idle_action_time = self._next_idle_time()

        # ── Physical behaviours ───────────────────────────────────────────────
        self.balance_enabled = kwargs.get('balance_enabled', True)
        self.chicken_head_enabled = kwargs.get('chicken_head_enabled', False)
        self.track_people = kwargs.get('track_people', True)
        self.track_people_servos = kwargs.get('track_people_servos', False)
        self._last_euler = None

        # ── Dependency-injected hardware ─────────────────────────────────────
        self.servos = {}   # injected: Servo_* wildcard
        self.imu = {}      # injected: imu.head / imu.body

        # ── Vision reaction debounce ──────────────────────────────────────────
        self.object_reaction_end_time = None

        # ── Telegram routing ─────────────────────────────────────────────────
        self._pending_telegram_user_id = None

    # ── Messaging setup ───────────────────────────────────────────────────────

    def setup_messaging(self):
        """Subscribe to all relevant topics."""
        # System ticks
        self.subscribe('system/loop/1', self._on_second)
        self.subscribe('system/loop/10', self._on_ten_seconds)

        # Sensor inputs
        self.subscribe('gpio/motion', self._on_motion)
        self.subscribe('system/temperature', self._on_temperature)
        self.subscribe('system/debug/log_hz', self._on_hz_update)

        # Vision
        if self.track_people:
            self.subscribe('vision/detections', self._on_vision_detections)

        # Speech / AI pipeline
        self.subscribe('speech', self._on_speech_input)
        self.subscribe('ai/response', self._on_ai_response)

        # Messaging (Telegram etc.)
        self.subscribe('telegram/received', self._on_telegram_message)

        # Serial activity resets the interaction timer
        self.subscribe('serial', self._on_serial_activity)

    # ── State machine ─────────────────────────────────────────────────────────

    def _transition(self, new_state):
        """Move to a new state and trigger any entry actions."""
        if self.state == new_state:
            return
        old_state = self.state
        self.state = new_state
        self.log(f"State: {old_state} -> {new_state}")

        if new_state == self.STATE_SLEEPING:
            self._on_enter_sleep()
        elif new_state == self.STATE_IDLE:
            self._on_enter_idle()
        elif new_state == self.STATE_ATTENTIVE:
            self._on_enter_attentive()
        elif new_state == self.STATE_INTERACTING:
            self._on_enter_interacting()

    def _on_enter_sleep(self):
        self.publish('system/sleep', requestor='companion')
        self.publish('eye/blink')
        self.publish('led', identifiers=[0, 1, 2, 3, 4], color='off')
        self.publish('display/body/text', text='ZZZ', font_size=26)

    def _on_enter_idle(self):
        self.publish('system/wake', requestor='companion')
        self.publish('eye', color='blue')

    def _on_enter_attentive(self):
        self.publish('animate', action='level_neck')
        self.publish('eye', color='green')

    def _on_enter_interacting(self):
        self.publish('eye', color='yellow')

    # ── Sensor handlers ───────────────────────────────────────────────────────

    def _on_motion(self, value=None):
        """Wake from sleep on any motion; update interaction timer."""
        if value is not None:
            self.last_motion_time = time.time()
        if self.state == self.STATE_SLEEPING:
            self._transition(self.STATE_IDLE)
        self.last_interaction_time = time.time()

    def _on_temperature(self, value=None):
        """Track CPU temperature and tint the display red when hot."""
        if value is None:
            return
        self.temperature = float(value)
        if self.temperature > 70:
            rgba = self._temp_to_color(self.temperature)
            self.publish('display/background', color=rgba)
        else:
            self.publish('display/background', color='black')

    def _on_hz_update(self, hz=None):
        self.current_hz = hz

    def _on_serial_activity(self, type=None, identifier=None, message=None):
        self.last_interaction_time = time.time()

    # ── Vision ────────────────────────────────────────────────────────────────

    def _on_vision_detections(self, matches=None):
        """
        React to vision detections.

        - Tracks the nearest person with the eye display.
        - Optionally moves neck servos to follow them.
        - Transitions to attentive state.
        - Sends a greeting to the AI once per ``greeting_cooldown`` seconds.
        """
        if not matches:
            return
        now = time.time()

        # Filter to people only and pick the nearest (largest bounding box)
        people = [m for m in matches if m.get('category') == 'person']
        if not people:
            return
        people.sort(key=lambda m: m['bbox'][2] * m['bbox'][3], reverse=True)
        person = people[0]
        bbox = person['bbox']

        # Eye tracking (pubsub)
        if self.object_reaction_end_time is None or now >= self.object_reaction_end_time:
            self._track_person_eye(bbox)
            self.object_reaction_end_time = now + 0.5

        # Neck servo tracking (requires injected servos)
        if self.track_people_servos:
            self._track_person_servos(bbox)

        self.last_person_seen_time = now

        # Wake up and become attentive
        if self.state in (self.STATE_SLEEPING, self.STATE_IDLE):
            self._transition(self.STATE_ATTENTIVE)
        self.last_interaction_time = now

        # Greet the visitor if the cooldown has elapsed
        if self.last_greeting_time is None or now - self.last_greeting_time > self.greeting_cooldown:
            self.last_greeting_time = now
            self._greet_person()

    def _track_person_eye(self, bbox):
        """Convert bounding-box centre to eye-display coordinates and publish."""
        screen = (240, 240)
        camera = (640, 480)
        cx = bbox[0] + bbox[2] / 2
        cy = bbox[1] + bbox[3] / 2
        sx = int((cx / camera[0]) * screen[0])
        sy = int((cy / camera[1]) * screen[1])
        # Rotate 90° anticlockwise then flip horizontally to match display
        # orientation: (sx, sy) → (screen[0] - sy, screen[0] - sx)
        sx, sy = screen[0] - sy, screen[0] - sx
        # Scale to the inner 50% of the display to reduce jitter
        sx = int(sx * 0.5) + screen[0] // 4
        sy = int(sy * 0.5) + screen[1] // 4
        self.publish('eye/look', coordinates=(sx, sy))

    def _track_person_servos(self, bbox):
        """Move neck servos to keep the person centred in frame."""
        camera = (640, 480)
        threshold = 15  # degrees of tolerance before moving
        cx = bbox[0] + bbox[2] / 2
        cy = bbox[1] + bbox[3] / 2

        pan_angle = int(((cx - camera[0] / 2) / (camera[0] / 2)) * 40)
        if abs(pan_angle) > threshold and 'neck_pan' in self.servos:
            self.servos['neck_pan'].move_degrees(pan_angle)

        # Use the upper third of the bounding box for tilt (focus on the face)
        top_y = bbox[1] + 0.33 * bbox[3]
        tilt_angle = int(((top_y - camera[1] / 2) / (camera[1] / 2)) * 40)
        if abs(tilt_angle) > threshold and 'neck_tilt' in self.servos:
            self.servos['neck_tilt'].move_degrees(-tilt_angle)

    def _greet_person(self):
        """Ask the AI to generate a short greeting as Cody."""
        self.publish('animate', action='head_nod')
        self.publish(
            'ai/input',
            text=(
                "A person just appeared in front of you. "
                "Greet them warmly but briefly as Cody, a friendly companion robot."
            ),
        )

    # ── Speech / AI pipeline ─────────────────────────────────────────────────

    def _on_speech_input(self, text=None):
        """Route spoken text to the AI and transition to interacting."""
        if not text:
            return
        self._transition(self.STATE_INTERACTING)
        self.last_interaction_time = time.time()
        self.publish('ai/input', text=text)

    def _on_ai_response(self, response=None):
        """
        Handle an AI response.

        - Speaks the response aloud via TTS.
        - Plays a head-nod animation.
        - Routes the response back to a pending Telegram user if applicable.
        - Transitions back to attentive (or idle if no person recently seen).
        """
        if not response:
            return
        self.last_interaction_time = time.time()

        self.publish('tts', msg=response)
        self.publish('animate', action='head_nod')

        # Route to Telegram if this response was triggered by a Telegram message
        if self._pending_telegram_user_id is not None:
            self.publish(
                'telegram/respond',
                user_id=self._pending_telegram_user_id,
                message=response,
            )
            self._pending_telegram_user_id = None

        # Return to attentive if someone was recently seen, otherwise idle
        now = time.time()
        if self.last_person_seen_time and now - self.last_person_seen_time < 30:
            self._transition(self.STATE_ATTENTIVE)
        else:
            self._transition(self.STATE_IDLE)

    def _on_telegram_message(self, user_id=None, message=None):
        """Route an inbound Telegram message to the AI, preserving user_id."""
        if not message:
            return
        self._pending_telegram_user_id = user_id
        self._transition(self.STATE_INTERACTING)
        self.last_interaction_time = time.time()
        self.publish('ai/input', text=message)

    # ── Periodic ticks ────────────────────────────────────────────────────────

    def _on_second(self):
        """Called every second by the system loop."""
        now = time.time()

        # Physical stabilisation (requires injected hardware)
        self._balance()
        self._chicken_head()

        # Update display and status LEDs
        self._update_display()
        self._update_led_status()

        # Sleep management — transition when inactive long enough
        if (self.last_interaction_time
                and now - self.last_interaction_time > self.sleep_timeout
                and self.state != self.STATE_SLEEPING):
            self._transition(self.STATE_SLEEPING)

        # Idle behaviours
        if self.state == self.STATE_IDLE and now >= self.next_idle_action_time:
            self._do_idle_action()
            self.next_idle_action_time = self._next_idle_time()

    def _on_ten_seconds(self):
        """Called every ten seconds by the system loop."""
        # If the robot has been attentive for a while with no interaction, relax
        if (self.state == self.STATE_ATTENTIVE
                and self.last_person_seen_time
                and time.time() - self.last_person_seen_time > 20):
            self._transition(self.STATE_IDLE)

    # ── Idle behaviours ───────────────────────────────────────────────────────

    def _do_idle_action(self):
        """Pick and execute a random idle behaviour."""
        action = choice([self._idle_blink, self._idle_animation])
        action()

    def _idle_blink(self):
        self.publish('eye/blink')
        self.log("Idle: eye blink")

    def _idle_animation(self):
        animation = choice(self._IDLE_ANIMATIONS)
        self.log(f"Idle: animation '{animation}'")
        self.publish('animate', action='level_neck')
        self.publish('animate', action=animation)

    def _next_idle_time(self):
        return time.time() + randint(self.min_interval, self.max_interval)

    # ── Physical stabilisation ────────────────────────────────────────────────

    def _balance(self):
        """Use the body IMU to compensate for pitch by adjusting hip servos."""
        if not self.balance_enabled or 'body' not in self.imu:
            return
        euler = self.imu['body'].get_euler()
        if self._last_euler is None or any(
            abs(euler[i] - self._last_euler[i]) > 1 for i in range(len(euler))
        ):
            self._last_euler = euler
            pitch = euler[1]
            if abs(pitch) < 2:
                return
            if 'leg_l_hip' in self.servos and 'leg_r_hip' in self.servos:
                self.servos['leg_l_hip'].move_degrees(-pitch)
                self.servos['leg_r_hip'].move_degrees(pitch)

    def _chicken_head(self):
        """Use the head IMU to keep the head level (chicken-head stabilisation)."""
        if not self.chicken_head_enabled or 'head' not in self.imu:
            return
        euler = self.imu['head'].get_euler()
        yaw, pitch = euler[0], euler[1]
        zero_yaw = -yaw if yaw < 180 else 360 - yaw
        if abs(pitch) > 5 and 'neck_tilt' in self.servos:
            self.servos['neck_tilt'].move_degrees(pitch)
        if abs(zero_yaw) > 5 and 'neck_pan' in self.servos:
            self.servos['neck_pan'].move_degrees(zero_yaw)

    # ── Display management ────────────────────────────────────────────────────

    def _update_display(self):
        """Cycle through display information states every 5 seconds."""
        if time.time() - self.display_change >= 5:
            self.display_change = time.time()
            self.display_state = (self.display_state + 1) % 5

        {
            0: self._display_time,
            1: self._display_temperature,
            2: self._display_uptime,
            3: self._display_current_state,
            4: self._display_hz,
        }.get(self.display_state, self._display_time)()

    def _display_time(self):
        self.publish('display/body/text', text=time.strftime("%H:%M:%S"), font_size=26)

    def _display_temperature(self):
        temp = f"{self.temperature}°C" if self.temperature is not None else "?°C"
        self.publish('display/body/text', text=temp, font_size=26)

    def _display_uptime(self):
        uptime = int(time.time() - self.start_time)
        h, remainder = divmod(uptime, 3600)
        m, s = divmod(remainder, 60)
        self.publish('display/body/text', text=f"Up\n{h:02}:{m:02}:{s:02}", font_size=14)

    def _display_current_state(self):
        self.publish('display/body/text', text=f"Mode\n{self.state}", font_size=14)

    def _display_hz(self):
        self.publish('display/body/text', text=f"{self.current_hz}Hz", font_size=20)

    # ── LED status strip ─────────────────────────────────────────────────────

    def _update_led_status(self):
        """Shift a new state-coloured pixel through the status strip every 3 s."""
        now = time.time()
        if self.last_led_time and now - self.last_led_time < 3:
            return
        self.last_led_time = now

        color = self._STATE_LED.get(
            self.state,
            choice(['blue', 'purple', 'white_dim']),  # idle: random cool colour
        )
        # Shift existing colours along the strip
        for i in range(len(self.led_colors) - 1, 0, -1):
            self.led_colors[i] = self.led_colors[i - 1]
        self.led_colors[0] = color

        for i, c in enumerate(self.led_colors):
            self.publish('led', identifiers=[i], color=c)

        self.log(f"LED status: {color}", level='debug')

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _temp_to_color(temp, min_temp=70, max_temp=90):
        """Map a temperature value to a red-tinted RGBA tuple."""
        temp = max(min_temp, min(max_temp, temp))
        norm = (temp - min_temp) / (max_temp - min_temp)
        return (int(255 * norm), 0, 0, 255)

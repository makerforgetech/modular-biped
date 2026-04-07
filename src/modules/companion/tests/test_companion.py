import time
import unittest
from unittest.mock import MagicMock, patch, call

from modules.companion.companion import Companion


def _make_companion(**kwargs):
    """Return a Companion instance with a mock messaging service attached."""
    c = Companion(**kwargs)
    ms = MagicMock()
    ms.subscribe = MagicMock()
    ms.publish = MagicMock()
    c._messaging_service = ms
    # Manually call setup_messaging as the loader normally would after setting
    # the messaging service via its property setter.
    c.setup_messaging()
    return c


class TestCompanionInit(unittest.TestCase):

    def test_default_state_is_idle(self):
        c = Companion()
        self.assertEqual(c.state, Companion.STATE_IDLE)

    def test_custom_sleep_timeout(self):
        c = Companion(sleep_timeout=30)
        self.assertEqual(c.sleep_timeout, 30)

    def test_default_balance_enabled(self):
        c = Companion()
        self.assertTrue(c.balance_enabled)

    def test_injected_servos_and_imu_start_empty(self):
        c = Companion()
        self.assertEqual(c.servos, {})
        self.assertEqual(c.imu, {})


class TestCompanionStateMachine(unittest.TestCase):

    def setUp(self):
        self.c = _make_companion()

    def test_transition_idle_to_attentive(self):
        self.c._transition(Companion.STATE_ATTENTIVE)
        self.assertEqual(self.c.state, Companion.STATE_ATTENTIVE)

    def test_transition_idle_to_sleeping(self):
        self.c._transition(Companion.STATE_SLEEPING)
        self.assertEqual(self.c.state, Companion.STATE_SLEEPING)
        # Should publish system/sleep
        self.c._messaging_service.publish.assert_any_call(
            'system/sleep', requestor='companion'
        )

    def test_no_transition_to_same_state(self):
        publish_count = self.c._messaging_service.publish.call_count
        self.c._transition(Companion.STATE_IDLE)
        self.assertEqual(self.c._messaging_service.publish.call_count, publish_count)

    def test_wake_publishes_system_wake(self):
        self.c.state = Companion.STATE_SLEEPING
        self.c._transition(Companion.STATE_IDLE)
        self.c._messaging_service.publish.assert_any_call(
            'system/wake', requestor='companion'
        )


class TestCompanionMotionHandler(unittest.TestCase):

    def setUp(self):
        self.c = _make_companion()

    def test_motion_wakes_from_sleep(self):
        self.c.state = Companion.STATE_SLEEPING
        self.c._on_motion(value=5)
        self.assertEqual(self.c.state, Companion.STATE_IDLE)

    def test_motion_updates_interaction_time(self):
        before = self.c.last_interaction_time
        time.sleep(0.05)
        self.c._on_motion(value=0)
        self.assertGreater(self.c.last_interaction_time, before)

    def test_motion_does_not_change_state_when_already_idle(self):
        self.c.state = Companion.STATE_IDLE
        self.c._on_motion(value=0)
        self.assertEqual(self.c.state, Companion.STATE_IDLE)


class TestCompanionSpeechAIPipeline(unittest.TestCase):

    def setUp(self):
        self.c = _make_companion()

    def test_speech_routes_to_ai_input(self):
        self.c._on_speech_input(text='Hello Cody')
        self.c._messaging_service.publish.assert_any_call('ai/input', text='Hello Cody')

    def test_speech_transitions_to_interacting(self):
        self.c._on_speech_input(text='Hello')
        self.assertEqual(self.c.state, Companion.STATE_INTERACTING)

    def test_empty_speech_is_ignored(self):
        publish_count = self.c._messaging_service.publish.call_count
        self.c._on_speech_input(text='')
        self.assertEqual(self.c._messaging_service.publish.call_count, publish_count)

    def test_ai_response_triggers_tts_and_animation(self):
        self.c._on_ai_response(response='Hello there!')
        self.c._messaging_service.publish.assert_any_call('tts', msg='Hello there!')
        self.c._messaging_service.publish.assert_any_call('animate', action='head_nod')

    def test_ai_response_routes_to_telegram_when_pending(self):
        self.c._pending_telegram_user_id = 42
        self.c._on_ai_response(response='Hi!')
        self.c._messaging_service.publish.assert_any_call(
            'telegram/respond', user_id=42, message='Hi!'
        )
        self.assertIsNone(self.c._pending_telegram_user_id)

    def test_ai_response_does_not_publish_telegram_without_pending(self):
        self.c._pending_telegram_user_id = None
        self.c._on_ai_response(response='Hi!')
        calls = [str(c) for c in self.c._messaging_service.publish.call_args_list]
        self.assertFalse(any('telegram/respond' in c for c in calls))


class TestCompanionTelegramPipeline(unittest.TestCase):

    def setUp(self):
        self.c = _make_companion()

    def test_telegram_message_routes_to_ai(self):
        self.c._on_telegram_message(user_id=7, message='What time is it?')
        self.c._messaging_service.publish.assert_any_call(
            'ai/input', text='What time is it?'
        )
        self.assertEqual(self.c._pending_telegram_user_id, 7)

    def test_telegram_transitions_to_interacting(self):
        self.c._on_telegram_message(user_id=7, message='Hi')
        self.assertEqual(self.c.state, Companion.STATE_INTERACTING)


class TestCompanionSleepManagement(unittest.TestCase):

    def setUp(self):
        self.c = _make_companion(sleep_timeout=1)

    def test_sleeps_after_timeout(self):
        self.c.last_interaction_time = time.time() - (self.c.sleep_timeout + 1)
        self.c._on_second()
        self.assertEqual(self.c.state, Companion.STATE_SLEEPING)

    def test_does_not_sleep_when_recently_active(self):
        self.c.last_interaction_time = time.time()
        self.c._on_second()
        self.assertNotEqual(self.c.state, Companion.STATE_SLEEPING)


class TestCompanionTemperatureToColor(unittest.TestCase):

    def test_below_min_is_black(self):
        color = Companion._temp_to_color(60)
        self.assertEqual(color[0], 0)

    def test_above_max_is_full_red(self):
        color = Companion._temp_to_color(95)
        self.assertEqual(color[0], 255)

    def test_midpoint_is_half_red(self):
        color = Companion._temp_to_color(80)
        self.assertAlmostEqual(color[0], 127, delta=1)


class TestCompanionVisionDetections(unittest.TestCase):

    def setUp(self):
        self.c = _make_companion()

    def test_no_people_does_not_transition(self):
        self.c._on_vision_detections(matches=[
            {'category': 'cat', 'bbox': (10, 10, 50, 50)}
        ])
        self.assertEqual(self.c.state, Companion.STATE_IDLE)

    def test_person_transitions_to_attentive(self):
        self.c._on_vision_detections(matches=[
            {'category': 'person', 'bbox': (10, 10, 100, 200)}
        ])
        self.assertEqual(self.c.state, Companion.STATE_ATTENTIVE)

    def test_person_triggers_greeting_on_first_detection(self):
        self.c._on_vision_detections(matches=[
            {'category': 'person', 'bbox': (10, 10, 100, 200)}
        ])
        self.c._messaging_service.publish.assert_any_call(
            'animate', action='head_nod'
        )
        # ai/input should have been published for the greeting
        ai_calls = [
            c for c in self.c._messaging_service.publish.call_args_list
            if c.args and c.args[0] == 'ai/input'
        ]
        self.assertTrue(len(ai_calls) > 0)

    def test_greeting_cooldown_prevents_double_greeting(self):
        self.c._on_vision_detections(matches=[
            {'category': 'person', 'bbox': (10, 10, 100, 200)}
        ])
        first_call_count = self.c._messaging_service.publish.call_count
        self.c._on_vision_detections(matches=[
            {'category': 'person', 'bbox': (10, 10, 100, 200)}
        ])
        # Second detection should not add another ai/input greeting call
        ai_calls_after = [
            c for c in self.c._messaging_service.publish.call_args_list
            if c.args and c.args[0] == 'ai/input'
        ]
        self.assertEqual(len(ai_calls_after), 1)


if __name__ == '__main__':
    unittest.main()

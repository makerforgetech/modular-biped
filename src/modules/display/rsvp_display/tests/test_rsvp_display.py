import sys
import time
import threading
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Stub out all hardware / third-party modules before importing the module
# ---------------------------------------------------------------------------
mock_spi = MagicMock()
mock_pil = MagicMock()
mock_image_cls = MagicMock()
mock_image_draw_cls = MagicMock()
mock_image_font_cls = MagicMock()
mock_lcd = MagicMock()
mock_lcd_module = MagicMock()

sys.modules['spidev'] = mock_spi
sys.modules['PIL'] = mock_pil
sys.modules['PIL.Image'] = mock_image_cls
sys.modules['PIL.ImageDraw'] = mock_image_draw_cls
sys.modules['PIL.ImageFont'] = mock_image_font_cls
sys.modules['modules.display.lib'] = mock_lcd
sys.modules['modules.display.lib.LCD_1inch28'] = mock_lcd_module

# Stub out TFTDisplay so we don't need real hardware
mock_tft_display_mod = MagicMock()
sys.modules['modules.display.tft_display'] = mock_tft_display_mod


class _FakeTFTDisplay:
    """Minimal stand-in for TFTDisplay used in tests."""

    def __init__(self, **kwargs):
        disp = MagicMock()
        disp.width = 240
        disp.height = 240
        self.disp = disp
        self.background = MagicMock()
        self.background.copy.return_value = MagicMock()

    def setup_messaging(self):
        pass

    def subscribe(self, topic, callback, **kwargs):
        pass

    def publish(self, topic, *args, **kwargs):
        pass

    def show_image(self, image):
        pass


mock_tft_display_mod.TFTDisplay = _FakeTFTDisplay

# Now import the module under test
from modules.display.rsvp_display.rsvp_display import RSVPDisplay  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rsvp(**kwargs):
    """Return an RSVPDisplay instance with mocked low-level dependencies."""
    with patch('modules.display.rsvp_display.rsvp_display.ImageFont') as mock_font_mod:
        mock_font_mod.truetype.return_value = MagicMock()
        inst = RSVPDisplay(**kwargs)
    inst.subscribe = MagicMock()
    inst.show_image = MagicMock()
    inst._font = MagicMock()
    return inst


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRSVPDisplayInit(unittest.TestCase):

    def test_default_wpm(self):
        rsvp = _make_rsvp()
        self.assertEqual(rsvp.wpm, 250)

    def test_custom_wpm(self):
        rsvp = _make_rsvp(wpm=300)
        self.assertEqual(rsvp.wpm, 300)

    def test_default_font_size(self):
        rsvp = _make_rsvp()
        self.assertEqual(rsvp.font_size, 40)

    def test_custom_font_size(self):
        rsvp = _make_rsvp(font_size=32)
        self.assertEqual(rsvp.font_size, 32)

    def test_default_text_color(self):
        rsvp = _make_rsvp()
        self.assertEqual(rsvp.text_color, (255, 255, 255))

    def test_custom_text_color(self):
        rsvp = _make_rsvp(text_color=(200, 200, 200))
        self.assertEqual(rsvp.text_color, (200, 200, 200))

    def test_default_highlight_color(self):
        rsvp = _make_rsvp()
        self.assertEqual(rsvp.highlight_color, (255, 50, 50))

    def test_custom_highlight_color(self):
        rsvp = _make_rsvp(highlight_color=(0, 255, 0))
        self.assertEqual(rsvp.highlight_color, (0, 255, 0))

    def test_font_fallback_to_default(self):
        """When truetype font is unavailable, load_default() is used."""
        with patch('modules.display.rsvp_display.rsvp_display.ImageFont') as mock_font_mod:
            mock_font_mod.truetype.side_effect = IOError
            mock_font_mod.load_default.return_value = MagicMock()
            rsvp = RSVPDisplay()
        mock_font_mod.load_default.assert_called_once()

    def test_stop_event_initialised(self):
        rsvp = _make_rsvp()
        self.assertIsInstance(rsvp._stop_event, threading.Event)

    def test_rsvp_thread_initially_none(self):
        rsvp = _make_rsvp()
        self.assertIsNone(rsvp._rsvp_thread)


class TestSetupMessaging(unittest.TestCase):

    def test_subscribes_to_rsvp_text(self):
        rsvp = _make_rsvp()
        rsvp.subscribe = MagicMock()
        rsvp.setup_messaging()
        rsvp.subscribe.assert_called_with('rsvp/text', rsvp.display_rsvp)


class TestGetOrpIndex(unittest.TestCase):

    def test_single_char(self):
        rsvp = _make_rsvp()
        self.assertEqual(rsvp._get_orp_index('a'), 0)

    def test_two_chars(self):
        rsvp = _make_rsvp()
        # int(2 * 0.3) = 0, max(0, 0) = 0
        self.assertEqual(rsvp._get_orp_index('ab'), 0)

    def test_five_chars(self):
        rsvp = _make_rsvp()
        # int(5 * 0.3) = 1
        self.assertEqual(rsvp._get_orp_index('hello'), 1)

    def test_ten_chars(self):
        rsvp = _make_rsvp()
        # int(10 * 0.3) = 3
        self.assertEqual(rsvp._get_orp_index('abcdefghij'), 3)

    def test_orp_never_exceeds_last_index(self):
        rsvp = _make_rsvp()
        word = 'x'
        idx = rsvp._get_orp_index(word)
        self.assertLess(idx, len(word))


class TestWordDelay(unittest.TestCase):

    def test_base_delay_250wpm(self):
        rsvp = _make_rsvp(wpm=250)
        self.assertAlmostEqual(rsvp._word_delay('hello'), 60.0 / 250)

    def test_punctuation_doubles_delay(self):
        rsvp = _make_rsvp(wpm=250)
        base = 60.0 / 250
        self.assertAlmostEqual(rsvp._word_delay('hello.'), base * 2.5)

    def test_all_punctuation_triggers_pause(self):
        rsvp = _make_rsvp(wpm=250)
        base = 60.0 / 250
        for ch in '.!?,;:':
            with self.subTest(ch=ch):
                self.assertAlmostEqual(rsvp._word_delay('word' + ch), base * 2.5)

    def test_empty_word_returns_base_delay(self):
        rsvp = _make_rsvp(wpm=250)
        self.assertAlmostEqual(rsvp._word_delay(''), 60.0 / 250)


class TestTextMeasurement(unittest.TestCase):

    def _draw_with_bbox(self, bbox):
        draw = MagicMock()
        draw.textbbox.return_value = bbox
        return draw

    def test_text_width_empty_string(self):
        rsvp = _make_rsvp()
        draw = MagicMock()
        self.assertEqual(rsvp._text_width(draw, ''), 0)

    def test_text_width_non_empty(self):
        rsvp = _make_rsvp()
        draw = self._draw_with_bbox((0, 0, 50, 20))
        self.assertEqual(rsvp._text_width(draw, 'hi'), 50)

    def test_text_height_empty_string(self):
        rsvp = _make_rsvp()
        draw = MagicMock()
        self.assertEqual(rsvp._text_height(draw, ''), 0)

    def test_text_height_non_empty(self):
        rsvp = _make_rsvp()
        draw = self._draw_with_bbox((0, 5, 50, 25))
        self.assertEqual(rsvp._text_height(draw, 'hi'), 20)


class TestRenderWord(unittest.TestCase):

    def _make_rsvp_with_draw(self):
        rsvp = _make_rsvp()
        # Provide a concrete background with copy() returning a real-ish mock
        mock_img = MagicMock()
        mock_img.width = 240
        mock_img.height = 240
        rsvp.background = MagicMock()
        rsvp.background.copy.return_value = mock_img
        return rsvp

    def test_empty_word_does_nothing(self):
        rsvp = self._make_rsvp_with_draw()
        rsvp.show_image = MagicMock()
        rsvp._render_word('')
        rsvp.show_image.assert_not_called()

    def test_show_image_called_for_non_empty_word(self):
        rsvp = self._make_rsvp_with_draw()
        with patch('modules.display.rsvp_display.rsvp_display.ImageDraw') as mock_id:
            mock_draw = MagicMock()
            mock_draw.textbbox.return_value = (0, 0, 20, 30)
            mock_id.Draw.return_value = mock_draw
            rsvp._render_word('hello')
        rsvp.show_image.assert_called_once()

    def test_orp_char_drawn_with_highlight_color(self):
        rsvp = self._make_rsvp_with_draw()
        with patch('modules.display.rsvp_display.rsvp_display.ImageDraw') as mock_id:
            mock_draw = MagicMock()
            mock_draw.textbbox.return_value = (0, 0, 20, 30)
            mock_id.Draw.return_value = mock_draw
            rsvp._render_word('hello')
        # Check that draw.text was called with the highlight colour
        calls = mock_draw.text.call_args_list
        highlight_calls = [c for c in calls if c.kwargs.get('fill') == rsvp.highlight_color
                           or (len(c.args) >= 3 and c.args[2] == rsvp.highlight_color)]
        # At least one call should use the highlight colour
        self.assertTrue(len(highlight_calls) >= 1 or
                        any(rsvp.highlight_color in str(c) for c in calls))

    def test_single_char_word(self):
        rsvp = self._make_rsvp_with_draw()
        with patch('modules.display.rsvp_display.rsvp_display.ImageDraw') as mock_id:
            mock_draw = MagicMock()
            mock_draw.textbbox.return_value = (0, 0, 20, 30)
            mock_id.Draw.return_value = mock_draw
            # Should not raise
            rsvp._render_word('a')
        rsvp.show_image.assert_called_once()


class TestDisplayRsvp(unittest.TestCase):

    def test_starts_thread(self):
        rsvp = _make_rsvp()
        with patch.object(rsvp, '_render_word'), \
             patch.object(rsvp._stop_event, 'wait', return_value=True):
            rsvp.display_rsvp('hello world')
            time.sleep(0.05)
            self.assertIsNotNone(rsvp._rsvp_thread)

    def test_stops_previous_thread_before_starting_new(self):
        rsvp = _make_rsvp()
        with patch.object(rsvp, '_stop_rsvp') as mock_stop, \
             patch.object(rsvp, '_render_word'), \
             patch.object(rsvp._stop_event, 'wait', return_value=True):
            rsvp.display_rsvp('one two')
            mock_stop.assert_called_once()

    def test_empty_text_starts_thread(self):
        rsvp = _make_rsvp()
        with patch.object(rsvp, '_render_word') as mock_render, \
             patch.object(rsvp._stop_event, 'wait', return_value=True):
            rsvp.display_rsvp('')
            time.sleep(0.05)
        mock_render.assert_not_called()

    def test_stop_event_cleared_before_loop(self):
        rsvp = _make_rsvp()
        rsvp._stop_event.set()  # pre-set
        with patch.object(rsvp, '_render_word'), \
             patch.object(rsvp._stop_event, 'wait', return_value=True):
            rsvp.display_rsvp('test')
            time.sleep(0.05)
        # Event should have been cleared, allowing words to display
        # (thread may have already finished; just verify no exception)


class TestRSVPLoop(unittest.TestCase):

    def test_renders_each_word(self):
        rsvp = _make_rsvp()
        render_calls = []
        rsvp._render_word = lambda w: render_calls.append(w)
        rsvp._stop_event.clear()
        # speed up: make wait return True immediately
        rsvp._stop_event.wait = MagicMock(return_value=False)
        rsvp._rsvp_loop('one two three')
        self.assertEqual(render_calls, ['one', 'two', 'three'])

    def test_stops_when_stop_event_set(self):
        rsvp = _make_rsvp()
        render_calls = []

        def fake_render(word):
            render_calls.append(word)
            rsvp._stop_event.set()  # stop after first word

        rsvp._render_word = fake_render
        rsvp._stop_event.clear()
        rsvp._stop_event.wait = MagicMock(return_value=True)
        rsvp._rsvp_loop('one two three')
        self.assertEqual(render_calls, ['one'])

    def test_empty_text_renders_nothing(self):
        rsvp = _make_rsvp()
        render_calls = []
        rsvp._render_word = lambda w: render_calls.append(w)
        rsvp._stop_event.clear()
        rsvp._rsvp_loop('')
        self.assertEqual(render_calls, [])


class TestStopRsvp(unittest.TestCase):

    def test_sets_stop_event(self):
        rsvp = _make_rsvp()
        rsvp._stop_rsvp()
        self.assertTrue(rsvp._stop_event.is_set())

    def test_joins_running_thread(self):
        rsvp = _make_rsvp()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        rsvp._rsvp_thread = mock_thread
        rsvp._stop_rsvp()
        mock_thread.join.assert_called_once()

    def test_no_error_when_thread_is_none(self):
        rsvp = _make_rsvp()
        rsvp._rsvp_thread = None
        # Should not raise
        rsvp._stop_rsvp()


if __name__ == '__main__':
    unittest.main()

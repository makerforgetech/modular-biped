import threading
import time
from PIL import Image, ImageDraw, ImageFont
from modules.display.tft_display import TFTDisplay


class RSVPDisplay(TFTDisplay):
    """
    Rapid Serial Visual Presentation (RSVP) display module.

    Subscribes to 'rsvp/text' and renders the received string one word at a time
    on the SPI TFT display.  Each word is shown with the Optimal Recognition Point
    (ORP) character highlighted in a configurable colour and aligned to a fixed
    horizontal position so the reader's eye never has to move.

    Configuration kwargs
    --------------------
    wpm : int
        Words per minute rate (default 250).
    font_size : int
        Font size in pixels (default 40).
    text_color : tuple
        RGB colour for normal characters, e.g. (255, 255, 255) for white.
    highlight_color : tuple
        RGB colour for the ORP character, e.g. (255, 50, 50) for red.
    """

    PUNCTUATION = frozenset('.!?,;:')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wpm = kwargs.get('wpm', 250)
        self.font_size = kwargs.get('font_size', 40)
        self.text_color = tuple(kwargs.get('text_color', (255, 255, 255)))
        self.highlight_color = tuple(kwargs.get('highlight_color', (255, 50, 50)))
        self._stop_event = threading.Event()
        self._rsvp_thread = None
        try:
            self._font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', self.font_size)
        except (IOError, OSError):
            self._font = ImageFont.load_default()

    def setup_messaging(self):
        super().setup_messaging()
        self.subscribe('rsvp/text', self.display_rsvp)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def display_rsvp(self, text):
        """Start displaying *text* in RSVP format.  Any ongoing sequence is stopped first."""
        self._stop_rsvp()
        self._stop_event.clear()
        self._rsvp_thread = threading.Thread(
            target=self._rsvp_loop,
            args=(text,),
            daemon=True,
        )
        self._rsvp_thread.start()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stop_rsvp(self):
        """Signal the current RSVP thread to stop and wait for it."""
        self._stop_event.set()
        if self._rsvp_thread and self._rsvp_thread.is_alive():
            self._rsvp_thread.join()

    def _rsvp_loop(self, text):
        words = text.split()
        for word in words:
            if self._stop_event.is_set():
                break
            self._render_word(word)
            delay = self._word_delay(word)
            self._stop_event.wait(timeout=delay)

    def _get_orp_index(self, word):
        """Return the index of the Optimal Recognition Point character."""
        length = len(word)
        if length <= 1:
            return 0
        # ORP sits at ~30 % into the word (0-based, clamped to valid range)
        return max(0, min(length - 1, int(length * 0.3)))

    def _word_delay(self, word):
        """Return display duration (seconds) for *word* at the configured WPM."""
        base = 60.0 / self.wpm
        if word and word[-1] in self.PUNCTUATION:
            return base * 2.5
        return base

    def _render_word(self, word):
        """Draw *word* on a black background with the ORP character highlighted."""
        if not word:
            return

        orp_idx = self._get_orp_index(word)
        left_part = word[:orp_idx]
        orp_char = word[orp_idx]
        right_part = word[orp_idx + 1:]

        img = self.background.copy()
        draw = ImageDraw.Draw(img)

        width = img.width
        height = img.height
        y_center = height // 2

        # Measure individual segment widths
        left_w = self._text_width(draw, left_part)
        orp_w = self._text_width(draw, orp_char)

        # The ORP character is anchored at the horizontal centre of the display
        orp_x = width // 2 - orp_w // 2
        left_x = orp_x - left_w
        right_x = orp_x + orp_w

        # Vertical position: centre the text
        text_h = self._text_height(draw, orp_char)
        y = y_center - text_h // 2

        if left_part:
            draw.text((left_x, y), left_part, font=self._font, fill=self.text_color)
        draw.text((orp_x, y), orp_char, font=self._font, fill=self.highlight_color)
        if right_part:
            draw.text((right_x, y), right_part, font=self._font, fill=self.text_color)

        self.show_image(img)

    def _text_width(self, draw, text):
        """Return the pixel width of *text* using the current font."""
        if not text:
            return 0
        bbox = draw.textbbox((0, 0), text, font=self._font)
        return bbox[2] - bbox[0]

    def _text_height(self, draw, text):
        """Return the pixel height of *text* using the current font."""
        if not text:
            return 0
        bbox = draw.textbbox((0, 0), text, font=self._font)
        return bbox[3] - bbox[1]

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
        print('Initializing RSVPDisplay with config: ' + str(kwargs))
        self.test_on_boot = kwargs.get('test_on_boot', False)
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

    def on_load(self):
        if self.test_on_boot:
            self.display_rsvp('This is an RSVP Display. It shows one word at a time with the optimal recognition point highlighted.')
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def display_rsvp(self, text):
        """Start displaying *text* in RSVP format.  Any ongoing sequence is stopped first."""
        self.log('Received text for RSVP display: ' + str(text))
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
        orp_x = self._compute_sentence_orp_x(words)
        for word in words:
            if self._stop_event.is_set():
                break
            self._render_word(word, orp_x)
            delay = self._word_delay(word)
            self._stop_event.wait(timeout=delay)

    def _compute_sentence_orp_x(self, words):
        """Return a fixed ORP x position for all words in the sentence.

        Each word is measured as if it were centred on the display, and the
        resulting ORP left-edge positions are averaged so that the highlighted
        character stays roughly stationary while words appear centred.
        """
        if not words:
            return self.background.width // 2
        draw = ImageDraw.Draw(self.background)
        width = self.background.width
        positions = []
        for word in words:
            if not word:
                continue
            orp_idx = self._get_orp_index(word)
            left_w = self._text_width(draw, word[:orp_idx])
            orp_w = self._text_width(draw, word[orp_idx])
            right_w = self._text_width(draw, word[orp_idx + 1:])
            full_w = left_w + orp_w + right_w
            word_left_x = width // 2 - full_w // 2
            positions.append(word_left_x + left_w)
        return int(sum(positions) / len(positions))

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

    def _render_word(self, word, orp_x=None):
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

        # Use the pre-computed sentence ORP position, or fall back to centre
        if orp_x is None:
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

        self.show_image(img.rotate(self.rotation))

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

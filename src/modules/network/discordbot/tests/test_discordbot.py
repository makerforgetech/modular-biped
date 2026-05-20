import asyncio
import io
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# ---------------------------------------------------------------------------
# Stub out the 'discord' package so tests run without installing it.
# ---------------------------------------------------------------------------
discord_stub = types.ModuleType("discord")

# Minimal flag-container used for Intents.default()
class _Intents:
    message_content = False

    @staticmethod
    def default():
        return _Intents()

# Minimal discord.Thread sentinel
class _Thread:
    pass

# Minimal discord.DMChannel sentinel
class _DMChannel:
    pass

# Minimal discord.HTTPException
class _HTTPException(Exception):
    pass

discord_stub.Intents = _Intents
discord_stub.Thread = _Thread
discord_stub.DMChannel = _DMChannel
discord_stub.HTTPException = _HTTPException

# discord.Client used inside DiscordBot.__init__
class _Client:
    def __init__(self, intents=None):
        self.user = Mock()
        self.user.id = 999
        self._events = {}

    def event(self, coro):
        """Decorator that records event coroutines."""
        self._events[coro.__name__] = coro
        return coro

    def get_channel(self, channel_id):
        return None

    async def start(self, token):
        pass

    async def close(self):
        pass

discord_stub.Client = _Client

sys.modules["discord"] = discord_stub

# ---------------------------------------------------------------------------
# Now import the module under test (with discord already stubbed).
# ---------------------------------------------------------------------------
from modules.network.discordbot.discordbot import DiscordBot, _TextExtractor  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_urlopen(html_content=b""):
    """Return a context-manager mock for urllib.request.urlopen."""
    mock_resp = MagicMock()
    mock_resp.__enter__ = Mock(return_value=mock_resp)
    mock_resp.__exit__ = Mock(return_value=False)
    mock_resp.read.return_value = html_content
    return Mock(return_value=mock_resp)


def _make_bot(prompt="Test prompt", knowledge_sources=None, token="fake-token",
              urlopen_mock=None, footer=""):
    """Return a DiscordBot instance with background thread and network suppressed."""
    if urlopen_mock is None:
        urlopen_mock = _mock_urlopen(b"")
    with patch("threading.Thread") as mock_thread, \
         patch.dict("os.environ", {"DISCORD_BOT_TOKEN": token}), \
         patch("modules.network.discordbot.discordbot.urllib.request.urlopen", urlopen_mock):
        mock_thread.return_value = Mock()
        bot = DiscordBot(
            prompt=prompt,
            knowledge_sources=knowledge_sources or [],
            footer=footer,
        )
        bot._loop = asyncio.new_event_loop()
        # Provide a messaging service so log() calls don't raise.
        bot._messaging_service = Mock()
        return bot


def _make_ai_mock(return_value="AI response"):
    """Return a mock ChatGPT instance whose text_completion() returns *return_value*."""
    mock_ai = Mock()
    mock_ai.text_completion.return_value = return_value
    return mock_ai


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTextExtractor(unittest.TestCase):
    """Tests for the HTML-to-text helper."""

    def test_plain_text_passthrough(self):
        ex = _TextExtractor()
        ex.feed("<p>Hello world</p>")
        self.assertEqual(ex.get_text(), "Hello world")

    def test_strips_script_content(self):
        ex = _TextExtractor()
        ex.feed("<p>Visible</p><script>secret()</script>")
        self.assertNotIn("secret", ex.get_text())
        self.assertIn("Visible", ex.get_text())

    def test_strips_style_content(self):
        ex = _TextExtractor()
        ex.feed("<style>.cls{color:red}</style><p>Content</p>")
        self.assertNotIn("color", ex.get_text())
        self.assertIn("Content", ex.get_text())

    def test_strips_nav_content(self):
        ex = _TextExtractor()
        ex.feed("<nav>Menu</nav><main>Article</main>")
        self.assertNotIn("Menu", ex.get_text())
        self.assertIn("Article", ex.get_text())

    def test_nested_skip_tags(self):
        """Nested skip tags should not expose intermediate content."""
        ex = _TextExtractor()
        ex.feed("<script><script>inner</script></script><p>after</p>")
        self.assertNotIn("inner", ex.get_text())
        self.assertIn("after", ex.get_text())


class TestDiscordBotInit(unittest.TestCase):
    """Tests for __init__ and configuration."""

    def test_raises_without_token(self):
        with patch.dict("os.environ", {}, clear=True), \
             patch("threading.Thread"):
            # Remove DISCORD_BOT_TOKEN if it happens to be set in the env.
            env = {k: v for k, v in __import__("os").environ.items()
                   if k != "DISCORD_BOT_TOKEN"}
            with patch.dict("os.environ", env, clear=True), \
                 patch("threading.Thread"):
                with self.assertRaises(RuntimeError):
                    DiscordBot()

    def test_token_from_env(self):
        bot = _make_bot(token="env-token")
        self.assertEqual(bot.token, "env-token")

    def test_system_prompt_no_sources(self):
        bot = _make_bot(prompt="Hello", knowledge_sources=[])
        self.assertEqual(bot.system_prompt, "Hello")

    def test_system_prompt_with_sources_contains_url(self):
        """The URL must appear in the system prompt (as a ### Source header)."""
        sources = ["https://example.com/wiki", "https://example.com/repo"]
        bot = _make_bot(prompt="Help me", knowledge_sources=sources)
        self.assertIn("https://example.com/wiki", bot.system_prompt)
        self.assertIn("https://example.com/repo", bot.system_prompt)
        self.assertIn("Help me", bot.system_prompt)

    def test_footer_defaults_to_empty(self):
        bot = _make_bot()
        self.assertEqual(bot.footer, "")

    def test_footer_from_kwarg(self):
        bot = _make_bot(footer="*Beta bot*")
        self.assertEqual(bot.footer, "*Beta bot*")

    def test_background_thread_started(self):
        with patch("threading.Thread") as mock_thread_cls, \
             patch.dict("os.environ", {"DISCORD_BOT_TOKEN": "tok"}), \
             patch("modules.network.discordbot.discordbot.urllib.request.urlopen",
                   _mock_urlopen(b"")):
            mock_thread = Mock()
            mock_thread_cls.return_value = mock_thread
            DiscordBot(prompt="p")
            mock_thread.start.assert_called_once()


class TestDiscordBotKnowledgeSources(unittest.TestCase):
    """Tests for knowledge-source URL fetching and prompt embedding."""

    def test_fetched_content_embedded_in_system_prompt(self):
        """Text content from a knowledge-source URL must appear in the prompt."""
        html = b"<html><body><p>Wiki article about modular-biped.</p></body></html>"
        bot = _make_bot(
            prompt="Base prompt",
            knowledge_sources=["https://example.com/wiki"],
            urlopen_mock=_mock_urlopen(html),
        )
        self.assertIn("Wiki article about modular-biped.", bot.system_prompt)
        self.assertIn("https://example.com/wiki", bot.system_prompt)

    def test_unavailable_source_shows_fallback_message(self):
        """When a URL cannot be fetched the prompt should note that gracefully."""
        failing_urlopen = Mock(side_effect=Exception("network error"))
        bot = _make_bot(
            prompt="Base prompt",
            knowledge_sources=["https://example.com/wiki"],
            urlopen_mock=failing_urlopen,
        )
        self.assertIn("https://example.com/wiki", bot.system_prompt)
        self.assertIn("could not be loaded", bot.system_prompt)

    def test_content_truncated_to_max_chars(self):
        """Fetched content must be truncated to max_chars_per_source."""
        long_text = ("word " * 2000).encode()  # ~10,000 chars
        html = b"<p>" + long_text + b"</p>"
        with patch("threading.Thread"), \
             patch.dict("os.environ", {"DISCORD_BOT_TOKEN": "tok"}), \
             patch("modules.network.discordbot.discordbot.urllib.request.urlopen",
                   _mock_urlopen(html)):
            bot = DiscordBot(
                prompt="p",
                knowledge_sources=["https://example.com"],
                max_chars_per_source=200,
            )
        # The embedded content section should not exceed 200 chars (plus "...").
        source_section = bot.system_prompt.split("### Source:")[-1]
        self.assertLessEqual(len(source_section.strip()), 300)
        self.assertTrue(source_section.strip().endswith("..."))

    def test_navigation_stripped_from_fetched_content(self):
        """<nav> content must be stripped before embedding."""
        html = (
            b"<nav>Home | About | Contact</nav>"
            b"<main><p>Actual article content here.</p></main>"
        )
        bot = _make_bot(
            prompt="p",
            knowledge_sources=["https://example.com"],
            urlopen_mock=_mock_urlopen(html),
        )
        self.assertIn("Actual article content here.", bot.system_prompt)
        self.assertNotIn("Home | About | Contact", bot.system_prompt)

    def test_fetch_knowledge_source_content_returns_none_on_error(self):
        """Static method returns None when the URL cannot be fetched."""
        with patch("modules.network.discordbot.discordbot.urllib.request.urlopen",
                   side_effect=Exception("timeout")):
            result = DiscordBot._fetch_knowledge_source_content("https://example.com")
        self.assertIsNone(result)

    def test_fetch_knowledge_source_content_strips_html(self):
        """Static method returns plain text, not raw HTML."""
        html = b"<html><body><h1>Title</h1><p>Body text.</p></body></html>"
        with patch("modules.network.discordbot.discordbot.urllib.request.urlopen",
                   _mock_urlopen(html)):
            result = DiscordBot._fetch_knowledge_source_content(
                "https://example.com", max_chars=1000
            )
        self.assertIn("Title", result)
        self.assertIn("Body text.", result)
        self.assertNotIn("<h1>", result)
        self.assertNotIn("<p>", result)

    def test_multiple_sources_all_embedded(self):
        """All knowledge-source URLs must have their content embedded."""
        html_a = b"<p>Content from source A.</p>"
        html_b = b"<p>Content from source B.</p>"
        responses = [_mock_urlopen(html_a)(), _mock_urlopen(html_b)()]
        side_effects = iter(responses)

        def urlopen_side_effect(req, timeout=10):
            return next(side_effects)

        with patch("threading.Thread"), \
             patch.dict("os.environ", {"DISCORD_BOT_TOKEN": "tok"}), \
             patch("modules.network.discordbot.discordbot.urllib.request.urlopen",
                   side_effect=urlopen_side_effect):
            bot = DiscordBot(
                prompt="p",
                knowledge_sources=["https://a.com", "https://b.com"],
            )
        self.assertIn("Content from source A.", bot.system_prompt)
        self.assertIn("Content from source B.", bot.system_prompt)


class TestDiscordBotMessaging(unittest.TestCase):
    """Tests for pubsub subscription and messaging helpers."""

    def setUp(self):
        self.bot = _make_bot()

    def test_setup_messaging_subscribes_to_topics(self):
        with patch.object(self.bot, "subscribe") as mock_sub:
            self.bot.setup_messaging()
            topics = [call[0][0] for call in mock_sub.call_args_list]
            self.assertIn("discord/send", topics)
            self.assertIn("system/exit", topics)
            self.assertNotIn("ai/response", topics)

    def test_handle_ai_response_stores_response(self):
        self.bot.handle_ai_response(response="Great answer!")
        self.assertEqual(self.bot._current_response, "Great answer!")

    def test_handle_send_missing_args_logs_warning(self):
        with patch.object(self.bot, "log") as mock_log:
            self.bot.handle_send(channel_id=None, message=None)
            mock_log.assert_called_once()
            _, kwargs = mock_log.call_args
            self.assertEqual(kwargs.get("level"), "warning")

    def test_handle_send_schedules_coroutine(self):
        with patch("asyncio.run_coroutine_threadsafe") as mock_rtf:
            self.bot.handle_send(channel_id=123, message="hi")
            mock_rtf.assert_called_once()

    def test_shutdown_wrapper_schedules_close(self):
        with patch("asyncio.run_coroutine_threadsafe") as mock_rtf:
            self.bot._shutdown_wrapper()
            mock_rtf.assert_called_once()


class TestDiscordBotGetAiResponse(unittest.TestCase):
    """Tests for the direct AI-request helper."""

    def setUp(self):
        self.bot = _make_bot()

    def test_returns_error_when_no_ai_instance(self):
        """When ai_instance is not set, returns an error string."""
        result = self.bot._get_ai_response("question")
        self.assertIn("[Error:", result)

    def test_calls_ai_instance_and_returns_response(self):
        """Calls ai_instance.text_completion() with the text and persona, and returns the result."""
        self.bot.ai_instance = _make_ai_mock("AI says hello")
        result = self.bot._get_ai_response("hello?")
        self.bot.ai_instance.text_completion.assert_called_once_with(
            "hello?", persona=self.bot.system_prompt
        )
        self.assertEqual(result, "AI says hello")

    def test_returns_none_when_ai_returns_none(self):
        """Propagates None from ai_instance.text_completion()."""
        self.bot.ai_instance = _make_ai_mock(None)
        result = self.bot._get_ai_response("q")
        self.assertIsNone(result)

    def test_returns_empty_string_when_ai_returns_empty(self):
        """Propagates empty string from ai_instance.text_completion()."""
        self.bot.ai_instance = _make_ai_mock("")
        result = self.bot._get_ai_response("q")
        self.assertEqual(result, "")

    def test_handles_exception_from_ai_instance(self):
        """Returns an error string when ai_instance.text_completion() raises."""
        mock_ai = Mock()
        mock_ai.text_completion.side_effect = Exception("boom")
        self.bot.ai_instance = mock_ai
        result = self.bot._get_ai_response("q")
        self.assertIn("[Error:", result)


class TestDiscordBotOnMessage(unittest.TestCase):
    """Tests for the async _on_message handler."""

    def setUp(self):
        self.bot = _make_bot()
        self.bot.ai_instance = _make_ai_mock("AI response")

    def _run(self, coro):
        return asyncio.run(coro)

    def _make_message(self, content="hello", in_thread=False, from_bot=False,
                      is_dm=False):
        msg = MagicMock()
        msg.content = content
        msg.created_at = "2024-01-01T00:00:00"
        # Use the actual bot user object so that identity comparisons work.
        msg.author = self.bot._bot.user if from_bot else MagicMock()
        msg.mentions = [] if is_dm else [self.bot._bot.user]
        msg.reply = AsyncMock()
        if in_thread:
            msg.channel = MagicMock(spec=discord_stub.Thread)
            msg.channel.send = AsyncMock()
            msg.channel.history = MagicMock(return_value=_async_iter([]))
        elif is_dm:
            msg.channel = MagicMock(spec=discord_stub.DMChannel)
            msg.channel.send = AsyncMock()
        else:
            msg.channel = MagicMock()
            msg.create_thread = AsyncMock(return_value=MagicMock(send=AsyncMock()))
        msg.id = 1
        return msg

    def test_ignores_own_messages(self):
        msg = self._make_message(from_bot=True)
        self._run(self.bot._on_message(msg))
        self.bot.ai_instance.text_completion.assert_not_called()

    def test_ignores_messages_without_mention(self):
        msg = self._make_message()
        msg.mentions = []  # bot not mentioned
        self._run(self.bot._on_message(msg))
        self.bot.ai_instance.text_completion.assert_not_called()

    def test_calls_ai_when_mentioned(self):
        msg = self._make_message(content=f"<@{self.bot._bot.user.id}> What is this?")
        self._run(self.bot._on_message(msg))
        self.bot.ai_instance.text_completion.assert_called_once()

    def test_creates_thread_for_channel_message(self):
        msg = self._make_message(
            content=f"<@{self.bot._bot.user.id}> Tell me more."
        )
        mock_thread = MagicMock()
        mock_thread.send = AsyncMock()
        msg.create_thread = AsyncMock(return_value=mock_thread)
        self.bot.ai_instance = _make_ai_mock("Sure!")
        self._run(self.bot._on_message(msg))
        msg.create_thread.assert_called_once()
        # The response should contain the AI's answer (plus the footer).
        sent_text = mock_thread.send.call_args[0][0]
        self.assertIn("Sure!", sent_text)

    def test_replies_in_existing_thread(self):
        msg = self._make_message(
            content=f"<@{self.bot._bot.user.id}> Explain.", in_thread=True
        )
        self.bot.ai_instance = _make_ai_mock("Explanation here.")
        self._run(self.bot._on_message(msg))
        sent_text = msg.channel.send.call_args[0][0]
        self.assertIn("Explanation here.", sent_text)

    def test_thread_context_included_in_ai_prompt(self):
        """Previous thread messages must be forwarded to the AI as context."""
        prior_msg = MagicMock()
        prior_msg.author = MagicMock()
        prior_msg.author.display_name = "Alice"
        prior_msg.content = "What is modular-biped?"
        prior_msg.id = 0  # Different from the current message id (1).

        msg = self._make_message(
            content=f"<@{self.bot._bot.user.id}> Can you elaborate?",
            in_thread=True,
        )
        msg.channel.history = MagicMock(return_value=_async_iter([prior_msg]))

        self._run(self.bot._on_message(msg))

        call_text = self.bot.ai_instance.text_completion.call_args[0][0]
        self.assertIn("Alice: What is modular-biped?", call_text)
        self.assertIn("Can you elaborate?", call_text)

    def test_empty_content_after_mention_still_calls_ai(self):
        """Empty content after stripping the @mention is still sent to the AI."""
        msg = self._make_message(content=f"<@{self.bot._bot.user.id}>")
        self._run(self.bot._on_message(msg))
        self.bot.ai_instance.text_completion.assert_called_once()
        call_text = self.bot.ai_instance.text_completion.call_args[0][0]
        self.assertIn("Question:", call_text)

    def test_footer_appended_to_response(self):
        """Configured footer must be appended to the AI response."""
        self.bot.footer = "*Beta bot.*"
        msg = self._make_message(content=f"<@{self.bot._bot.user.id}> Hi")
        mock_thread = MagicMock()
        mock_thread.send = AsyncMock()
        msg.create_thread = AsyncMock(return_value=mock_thread)
        self.bot.ai_instance = _make_ai_mock("Hello!")
        self._run(self.bot._on_message(msg))
        sent_text = mock_thread.send.call_args[0][0]
        self.assertIn("Hello!", sent_text)
        self.assertIn("*Beta bot.*", sent_text)

    def test_no_footer_when_empty(self):
        """When footer is empty no extra text should be appended."""
        self.bot.footer = ""
        msg = self._make_message(content=f"<@{self.bot._bot.user.id}> Hi")
        mock_thread = MagicMock()
        mock_thread.send = AsyncMock()
        msg.create_thread = AsyncMock(return_value=mock_thread)
        self.bot.ai_instance = _make_ai_mock("Exact answer")
        self._run(self.bot._on_message(msg))
        sent_text = mock_thread.send.call_args[0][0]
        self.assertEqual(sent_text, "Exact answer")

    # ------------------------------------------------------------------
    # DM (private message) tests
    # ------------------------------------------------------------------

    def test_responds_to_dm_without_mention(self):
        """DMs should be responded to without requiring a @mention."""
        msg = self._make_message(content="What is modular-biped?", is_dm=True)
        self.bot.ai_instance = _make_ai_mock("It is a robot project.")
        self._run(self.bot._on_message(msg))
        self.bot.ai_instance.text_completion.assert_called_once()
        msg.channel.send.assert_called_once()

    def test_dm_response_contains_ai_answer(self):
        """The response sent to a DM should contain the AI-generated text."""
        msg = self._make_message(content="Hello there!", is_dm=True)
        self.bot.ai_instance = _make_ai_mock("Hello human!")
        self._run(self.bot._on_message(msg))
        sent_text = msg.channel.send.call_args[0][0]
        self.assertIn("Hello human!", sent_text)

    def test_dm_does_not_create_thread(self):
        """DM responses must be sent directly to the channel, not via a thread."""
        msg = self._make_message(content="A question", is_dm=True)
        self.bot.ai_instance = _make_ai_mock("An answer")
        self._run(self.bot._on_message(msg))
        # create_thread should not have been called on the message.
        self.assertFalse(
            hasattr(msg, "create_thread") and msg.create_thread.called
        )
        msg.channel.send.assert_called_once()

    def test_ignores_own_dm(self):
        """The bot should ignore its own DM messages."""
        msg = self._make_message(content="test", is_dm=True, from_bot=True)
        self._run(self.bot._on_message(msg))
        self.bot.ai_instance.text_completion.assert_not_called()

    def test_dm_content_not_stripped_of_mentions(self):
        """DM content should be passed to the AI as-is (no mention stripping)."""
        msg = self._make_message(content="What is @someone doing?", is_dm=True)
        self._run(self.bot._on_message(msg))
        call_text = self.bot.ai_instance.text_completion.call_args[0][0]
        # The original question text should be preserved in the prompt.
        self.assertIn("What is @someone doing?", call_text)


class TestDiscordBotSendResponse(unittest.TestCase):
    """Tests for _send_response."""

    def setUp(self):
        self.bot = _make_bot()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_send_to_existing_thread(self):
        msg = MagicMock()
        msg.channel = MagicMock(spec=discord_stub.Thread)
        msg.channel.send = AsyncMock()
        self._run(self.bot._send_response(msg, "reply text"))
        msg.channel.send.assert_called_once_with("reply text")

    def test_send_to_dm_channel(self):
        """DM channel responses should be sent directly, not via a thread."""
        msg = MagicMock()
        msg.channel = MagicMock(spec=discord_stub.DMChannel)
        msg.channel.send = AsyncMock()
        self._run(self.bot._send_response(msg, "dm reply"))
        msg.channel.send.assert_called_once_with("dm reply")

    def test_creates_thread_in_channel(self):
        msg = MagicMock()
        msg.content = "short question"
        msg.channel = MagicMock()  # Not a Thread or DMChannel
        mock_thread = MagicMock()
        mock_thread.send = AsyncMock()
        msg.create_thread = AsyncMock(return_value=mock_thread)
        self._run(self.bot._send_response(msg, "answer"))
        msg.create_thread.assert_called_once()
        mock_thread.send.assert_called_once_with("answer")

    def test_fallback_on_http_exception(self):
        msg = MagicMock()
        msg.content = "question"
        msg.channel = MagicMock()
        msg.create_thread = AsyncMock(side_effect=discord_stub.HTTPException("err"))
        msg.reply = AsyncMock()
        self._run(self.bot._send_response(msg, "fallback"))
        msg.reply.assert_called_once_with("fallback")

    def test_long_content_truncated_in_thread_name(self):
        msg = MagicMock()
        msg.content = "x" * 200
        msg.channel = MagicMock()
        mock_thread = MagicMock()
        mock_thread.send = AsyncMock()
        msg.create_thread = AsyncMock(return_value=mock_thread)
        self._run(self.bot._send_response(msg, "resp"))
        call_kwargs = msg.create_thread.call_args[1]
        self.assertLessEqual(len(call_kwargs["name"]), 100)


class TestDiscordBotSendToChannel(unittest.TestCase):
    """Tests for _send_to_channel."""

    def setUp(self):
        self.bot = _make_bot()

    def _run(self, coro):
        return asyncio.run(coro)

    def test_sends_when_channel_found(self):
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        self.bot._bot.get_channel = Mock(return_value=mock_channel)
        self._run(self.bot._send_to_channel(123, "hello"))
        mock_channel.send.assert_called_once_with("hello")

    def test_logs_warning_when_channel_not_found(self):
        self.bot._bot.get_channel = Mock(return_value=None)
        with patch.object(self.bot, "log") as mock_log:
            self._run(self.bot._send_to_channel(999, "msg"))
            mock_log.assert_called_once()
            _, kwargs = mock_log.call_args
            self.assertEqual(kwargs.get("level"), "warning")


# ---------------------------------------------------------------------------
# Async iterator helper used in tests
# ---------------------------------------------------------------------------

class _async_iter:
    """Minimal async iterator for mocking discord channel history."""

    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration


if __name__ == "__main__":
    unittest.main()

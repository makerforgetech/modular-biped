import asyncio
import os
import threading
import urllib.request
from html.parser import HTMLParser

import discord
from modules.base_module import BaseModule

# Discord thread names are limited to 100 characters.  We reserve 3 for the
# trailing ellipsis ("...") so the effective content limit is 97 characters.
_MAX_THREAD_NAME_CONTENT = 97

# Default character limit applied to each fetched knowledge-source URL.
_DEFAULT_MAX_CHARS_PER_SOURCE = 5000


class _TextExtractor(HTMLParser):
    """Minimal HTML-to-text converter for extracting knowledge-source content."""

    # Tags whose content adds no meaningful text (scripts, navigation, etc.)
    _SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside"}

    def __init__(self):
        super().__init__()
        self._chunks = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._chunks.append(text)

    def get_text(self):
        return " ".join(self._chunks)


class DiscordBot(BaseModule):
    """
    Discord Bot module.

    Hosts a Discord bot that monitors for mentions and answers questions
    using the ChatGPT module directly (via ``ai_instance``) with
    GitHub-hosted knowledge sources specified in the config YAML.

    At startup the text content of each ``knowledge_sources`` URL is fetched
    and embedded directly into the system prompt so that ChatGPT can draw on
    the actual information rather than just seeing bare hyperlinks.  Each
    source is truncated to ``max_chars_per_source`` characters (default
    5,000) to keep prompt size manageable.

    The bot responds to:
    - Private messages (DMs): every message in a DM channel is processed
      without requiring the bot to be @mentioned.
    - Server channels / threads: the bot must be explicitly @mentioned.

    Any time the bot is triggered it will:
      1. Collect the thread context (if the post is already inside a thread).
      2. Forward the question together with the system prompt (which now
         contains the fetched knowledge) to the AI via
         ``ai_instance.completion()``.
      3. Post the reply back:
         - In a DM: directly in the DM channel.
         - In a thread: directly in that thread.
         - In a regular channel: create a new thread from the original post.

    Requires the environment variable ``DISCORD_BOT_TOKEN``.
    The ``ai_instance`` attribute must be set to a ``ChatGPT`` instance
    (e.g. via ``main.py``) before the bot will be able to answer questions.

    Subscribes to:
      - ``discord/send``    – allows other modules to send a message to a
                              specific channel (kwarg: channel_id, message)
      - ``system/exit``     – gracefully shuts down the bot

    Publishes to:
      - ``log/*``           – standard logging (via BaseModule.log)

    Example config (config/discordbot.yml):

        discordbot:
          enabled: true
          path: modules.network.discordbot.DiscordBot
          config:
            prompt: "You are a helpful assistant for the modular-biped project..."
            max_chars_per_source: 5000
            footer: "*I am a bot and currently in beta.*"
            knowledge_sources:
              - https://github.com/makerforgetech/modular-biped/wiki
              - https://github.com/makerforgetech/modular-biped/discussions
    """

    def __init__(self, **kwargs):
        """
        Initialise the Discord bot.

        :kwarg prompt: System prompt sent to the AI as the ``persona`` argument
            for every request.
        :kwarg knowledge_sources: List of URLs whose content will be fetched
            and embedded in the system prompt.
        :kwarg max_chars_per_source: Maximum characters to include from each
            fetched URL (default 5,000).
        :kwarg footer: Text appended to every AI response before posting to
            Discord.  Supports Markdown.
        :kwarg token: Bot token (falls back to DISCORD_BOT_TOKEN env var).
        """
        self.token = os.getenv("DISCORD_BOT_TOKEN", kwargs.get("token", None))
        if not self.token:
            raise RuntimeError(
                "DiscordBot: No DISCORD_BOT_TOKEN provided. "
                "Set it as an environment variable or pass it as a keyword argument."
            )

        self.ai_instance = None  # Will be set via set_chatgpt()

        self.prompt = kwargs.get(
            "prompt",
            "You are a helpful assistant. Answer questions clearly and concisely.",
        )
        self.knowledge_sources = kwargs.get("knowledge_sources", [])
        self.max_chars_per_source = kwargs.get(
            "max_chars_per_source", _DEFAULT_MAX_CHARS_PER_SOURCE
        )
        self.footer = kwargs.get("footer", "")

        # Build the system prompt, embedding fetched content from each URL so
        # ChatGPT can draw on the actual text rather than bare hyperlinks.
        if self.knowledge_sources:
            parts = [
                self.prompt,
                "\nKnowledge base (use this content to answer questions accurately):",
            ]
            for url in self.knowledge_sources:
                content = self._fetch_knowledge_source_content(
                    url, self.max_chars_per_source
                )
                if content:
                    parts.append(f"\n### Source: {url}\n{content}")
                else:
                    parts.append(f"\n### Source: {url}\n(Content could not be loaded)")
            self.system_prompt = "\n".join(parts)
        else:
            self.system_prompt = self.prompt

        # Serialise AI requests so that concurrent Discord mentions do not
        # interleave their pubsub publish/subscribe calls.
        self._ai_lock = threading.Lock()
        self._current_response = None

        # Set up Discord gateway intents.
        intents = discord.Intents.default()
        intents.message_content = True
        self._bot = discord.Client(intents=intents)

        # Register event handlers via decorators.
        @self._bot.event
        async def on_ready():
            self.log(f"Discord bot logged in as {self._bot.user}.")
            self.log(f"GPT instance set: {self.ai_instance is not None}")

        @self._bot.event
        async def on_message(message):
            await self._on_message(message)

        # Run the Discord client in a dedicated background thread so it does
        # not block the main system loop.
        self._loop = asyncio.new_event_loop()
        self._bot_thread = threading.Thread(
            target=self._run_bot,
            name="DiscordBotLoop",
            daemon=True,
        )
        self._bot_thread.start()

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def setup_messaging(self):
        """Subscribe to pubsub topics after the messaging service is set."""
        # self.subscribe("ai/response", self.handle_ai_response)
        self.subscribe("discord/send", self.handle_send)
        self.subscribe("system/exit", self._shutdown_wrapper)

    # ------------------------------------------------------------------
    # Bot lifecycle
    # ------------------------------------------------------------------
    
    def _run_bot(self):
        """Entry point for the background thread running the Discord event loop."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._bot.start(self.token))

    def _shutdown_wrapper(self, *args, **kwargs):
        """Schedule a clean shutdown of the Discord client."""
        self.log("Shutting down Discord bot...", level="info")
        asyncio.run_coroutine_threadsafe(self._bot.close(), self._loop)

    # ------------------------------------------------------------------
    # Incoming Discord messages
    # ------------------------------------------------------------------

    async def _on_message(self, message):
        """
        Called by discord.py for every message the bot can see.

        Responds to:
        - Any message in a private DM channel (no @mention required).
        - Messages in servers/threads where the bot is explicitly @mentioned.
        Does not respond to its own messages.
        """
        # print(f"Received message: {message.content} (mentions: {[m.display_name for m in message.mentions]})")

        if message.author == self._bot.user:
            return

        # Private messages: respond to everything without requiring a mention.
        is_dm = isinstance(message.channel, discord.DMChannel)

        if not is_dm and self._bot.user not in message.mentions:
            return

        self.log(f"Processing message from {message.author}: {message.content}", level="info")

        # Strip @mentions from content (only relevant for channel/thread messages).
        content = message.content
        if not is_dm:
            for mention in message.mentions:
                content = content.replace(f"<@{mention.id}>", "")
                content = content.replace(f"<@!{mention.id}>", "")
        content = content.strip()

        # If the message is already inside a thread, collect recent context.
        if isinstance(message.channel, discord.Thread):
            thread_lines = []
            async for msg in message.channel.history(limit=20, oldest_first=True):
                if msg.id != message.id:
                    thread_lines.append(
                        f"{msg.author.display_name}: {msg.content}"
                    )
            if thread_lines:
                context = "\n".join(thread_lines)
                full_text = (
                    f"Thread context:\n{context}\n\n"
                    f"Question: {content}"
                )
            else:
                full_text = f"Question: {content}"
        else:
            full_text = f"Question: {content}"

        # Offload the synchronous AI call to a thread-pool executor so the
        # Discord event loop is not blocked while waiting for the AI.
        
        # print(f"Full text sent to AI:\n{full_text}")
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, self._get_ai_response, full_text
        )

        if response:
            if self.footer:
                response += f"\n\n{self.footer}"
            # print (f"AI response:\n{response}")
            await self._send_response(message, response)
            
        # log the timestamp and full content of the message for debugging
        self.log(f"Received message at {message.created_at} from {message.author}: {message.content}\n\nFull text sent to AI:\n\n{full_text}\n\nResponse:\n\n{response}\n\nPrompt:{self.system_prompt}", level="file")

    # ------------------------------------------------------------------
    # AI integration (pubsub)
    # ------------------------------------------------------------------

    def _get_ai_response(self, text, prompt=None):
        """
        Call the ChatGPT module's completion() method directly.
        """
        if prompt is None:
            prompt = self.system_prompt
        if not self.ai_instance:
            self.log("ChatGPT instance not set in DiscordBot.", level="error")
            return "[Error: ChatGPT module not available]"
        try:
            return self.ai_instance.text_completion(text, persona=prompt)
        except Exception as e:
            self.log(f"Error calling ChatGPT completion: {e}", level="error")
            return f"[Error: {e}]"

    @staticmethod
    def _fetch_knowledge_source_content(url, max_chars=_DEFAULT_MAX_CHARS_PER_SOURCE):
        """
        Fetch *url* and return its text content, stripped of HTML markup.

        The result is truncated to *max_chars* characters.  Returns ``None``
        on any network or parsing error so callers can fall back gracefully.
        """
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; DiscordBot/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            extractor = _TextExtractor()
            extractor.feed(raw)
            # Collapse repeated whitespace for a cleaner prompt.
            text = " ".join(extractor.get_text().split())
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            return text or None
        except Exception:
            return None

    def handle_ai_response(self, response):
        """
        Receive an AI-generated response via the ``ai/response`` pubsub topic.

        :param response: The text generated by the AI module.
        """
        self._current_response = response

    # ------------------------------------------------------------------
    # Sending responses back to Discord
    # ------------------------------------------------------------------

    async def _send_response(self, message, response):
        """
        Send *response* back to Discord.

        - DM channels and existing threads: reply directly in the channel.
        - Regular server channels: create a new thread from the message so
          the conversation stays organised.
        """
        if len(response) > 2000:
            # split into chunks of 2000 characters and send as multiple messages to avoid Discord limits
            for i in range(0, len(response), 2000):
                chunk = response[i:i+2000]
                await self._send_response(message, chunk)
            return
        try:
            if isinstance(message.channel, (discord.Thread, discord.DMChannel)):
                await message.channel.send(response)
            else:
                thread_name = (message.content[:_MAX_THREAD_NAME_CONTENT] + "...") if len(message.content) > _MAX_THREAD_NAME_CONTENT else message.content
                thread_name = thread_name.strip() or "Discussion"
                try:
                    thread = await message.create_thread(name=thread_name)
                    await thread.send(response)
                except discord.HTTPException as e:
                    # Fallback: reply inline if thread creation fails.
                    self.log(f"Failed to create thread or send response in thread: {e}", level="error")
                    try:
                        await message.reply(response)
                    except Exception as e2:
                        self.log(f"Failed to reply inline after thread failure: {e2}", level="error")
        except Exception as e:
            self.log(f"Failed to send response: {e}", level="error")

    def handle_send(self, channel_id=None, message=None):
        """
        Send a message to a Discord channel from another module via pubsub.

        Publish ``discord/send`` with kwargs ``channel_id`` (int) and
        ``message`` (str) to use this handler.
        """
        if channel_id is None or message is None:
            self.log(
                "handle_send: channel_id and message are required",
                level="warning",
            )
            return
        asyncio.run_coroutine_threadsafe(
            self._send_to_channel(int(channel_id), message),
            self._loop,
        )

    async def _send_to_channel(self, channel_id, message):
        """Send *message* to the Discord channel identified by *channel_id*."""
        channel = self._bot.get_channel(channel_id)
        if channel:
            await channel.send(message)
        else:
            self.log(f"Channel {channel_id} not found", level="warning")

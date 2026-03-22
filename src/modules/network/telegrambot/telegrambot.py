#!/usr/bin/env python
# pylint: disable=unused-argument
import asyncio
import logging
import os
import threading
from modules.base_module import BaseModule

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

class TelegramBot(BaseModule):

    def __init__(self, **kwargs):
        """
        Telegram Bot
        :param kwargs: token

        Create a bot via Telegram's BotFather and get the token.
        
        Set the token as an environment variable 'TELEGRAM_BOT_TOKEN' (preferred) or pass it as a keyword argument.
        
        1. Search for BotFather in Telegram
        2. Start the BotFather
        3. Type /newbot
        4. Follow the instructions
        5. Copy the token (DON'T SHARE IT WITH ANYONE)
        6. Create an environment variable called TELEGRAM_BOT_TOKEN and set it to the token (can also be set in the config yaml)
        7. Run the script
        
        """
        # Get token from environment variable
        self.token = os.getenv('TELEGRAM_BOT_TOKEN', kwargs.get('token', None))
        if not self.token:
            raise RuntimeError("TelegramBot: No TELEGRAM_BOT_TOKEN provided. Set the token as an environment variable or pass it as a keyword argument.")
        # print(self.token)
        # Topics for pubsub communication
        raw_whitelist = kwargs.get('user_whitelist', [])
        normalized_whitelist = set()
        for candidate in raw_whitelist:
            try:
                normalized_whitelist.add(int(candidate))
            except (TypeError, ValueError):
                print(f"Skipping non-numeric whitelist entry '{candidate}'")

        admin_env = os.getenv('TELEGRAM_USER_ID', None)
        self.admin = None
        if admin_env is not None:
            try:
                self.admin = int(admin_env)
                normalized_whitelist.add(self.admin)
            except (TypeError, ValueError):
                print(f"Invalid TELEGRAM_USER_ID value '{admin_env}', skipping admin whitelist entry")

        self._startup_exception = None
        self._startup_error = threading.Event()
        self.user_whitelist = normalized_whitelist
        if not self.user_whitelist:
            print("User whitelist missing!")
        else:
            print(f"User whitelist: {sorted(self.user_whitelist)}")

        # Create the Application and pass it your bot's token
        self.application = Application.builder().token(self.token).build()

        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_event_loop, name="TelegramBotLoop", daemon=True)
        self._loop_thread.start()
        self._startup_future = None
        self._application_started = False
        self._bot_ready = threading.Event()
        self._chat_ids = {}
        self._updater_started = False

        # Set up command handlers
        self.application.add_handler(CommandHandler("start", TelegramBot.start))
        self.application.add_handler(CommandHandler("help", TelegramBot.help_command))

        # Set up message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_publish))
        
    def setup_messaging(self):
        self.subscribe('telegram/respond', self.handle_response_wrapper)
        # self.subscribe('telegram/received', self.handle_response_wrapper) # Test echoing received messages back to the user
        self.subscribe('system/exit', self._shutdown_wrapper)
        self._ensure_application_started()

    def _shutdown_wrapper(self, *args, **kwargs):
        self.log("[TelegramBot] Shutting down Telegram bot...", level='info')
        asyncio.run_coroutine_threadsafe(self.shutdown(), self._loop)
        
    def handle_response_wrapper(self, user_id=None, message=None):
        """Test method to verify the bot is working."""
        self.log(f"Received response to send to user {user_id}: {message}")
        if user_id is None or message is None:
            self.log("Missing user_id or message in response_wrapper; setting to admin", level='warning')
            user_id = self.admin
        asyncio.run_coroutine_threadsafe(self.handle_response(user_id, message), self._loop)

    def _run_event_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _ensure_application_started(self):
        if self._startup_future is not None:
            return

        async def start_application():
            await self.application.initialize()
            await self.application.start()
            if self.application.updater is not None:
                await self.application.updater.start_polling()
                self._updater_started = True
            self._application_started = True
            self._bot_ready.set()

        self._startup_future = asyncio.run_coroutine_threadsafe(start_application(), self._loop)
        self._startup_future.add_done_callback(self._handle_startup_result)

    def _handle_startup_result(self, future):
        exc = future.exception()
        if exc is not None:
            self.log(f"Failed to start Telegram application: {exc}", level='error')
            self._startup_exception = exc
            self._startup_error.set()

    async def shutdown(self):
        if not self._application_started:
            return
        if self._updater_started and self.application.updater is not None:
            await self.application.updater.stop()
            self._updater_started = False
        await self.application.stop()
        await self.application.shutdown()
        self._application_started = False
        self._loop.call_soon_threadsafe(self._loop.stop)

    async def _wait_until_ready(self, timeout=10.0):
        # Fail fast if startup error occurred
        if self._startup_error.is_set():
            raise RuntimeError(f"TelegramBot failed to start: {self._startup_exception}")
        waited = 0.0
        interval = 0.05
        while not self._application_started:
            if self._startup_error.is_set():
                raise RuntimeError(f"TelegramBot failed to start: {self._startup_exception}")
            await asyncio.sleep(interval)
            waited += interval
            if waited >= timeout:
                raise TimeoutError("TelegramBot: Timed out waiting for application to start.")

    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hi {user.mention_html()}!",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text("Help!")

    async def handle_publish(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Publish the user's message to the application via pubsub."""
        user_id = update.effective_user.id
        message = update.message.text
        
        # Check if user is in whitelist before processing
        if (user_id not in self.user_whitelist):
            self.log(f"User {user_id} not in whitelist, ignoring message", level='warning')
            return
        
        self.log(f"Received message from user {user_id}: {message}")

        chat = update.effective_chat
        if chat is not None:
            self._chat_ids[user_id] = chat.id
        
        # Save the update for response handling
        # Publish the message to other parts of the application
        self.publish('telegram/received', user_id=user_id, message=message)
        self.log(f"Published message from user {user_id}: {message} on topic telegram/received")

    async def handle_response(self, user_id: int, message: str) -> None:
        """Handle responses from the application and send them back to the user."""
        await self._wait_until_ready()
        if (user_id not in self.user_whitelist):
            self.log(f"User {user_id} not in whitelist, skipping response", level='warning')
            return
        self.log(f"Handling response for user {user_id}: {message}")
        chat_id = self._chat_ids.get(user_id)
        if chat_id is None:
            self.log(f"No chat history for user {user_id}; cannot deliver message", level='warning')
            return
        await self.application.bot.send_message(chat_id=chat_id, text=message)
    
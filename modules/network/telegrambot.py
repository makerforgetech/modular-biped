#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import logging
import os

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, **kwargs):
        """
        Telegram Bot
        :param kwargs: token
        
        Create a bot via Telegram's BotFather and get the token.
        
        1. Search for BotFather in Telegram
        2. Start the BotFather
        3. Type /newbot
        4. Follow the instructions
        5. Copy the token (DON'T SHARE IT WITH ANYONE)
        6. Create an environment variable called TELEGRAM_BOT_TOKEN and set it to the token (can also be set in the config yaml)
        7. Run the script
        
        """
        # get token from environment variable
        self.token = os.getenv('TELEGRAM_BOT_TOKEN', kwargs.get('token', None))
        
        """Start the bot."""
        # Create the Application and pass it your bot's token.
        application = Application.builder().token(self.token).build()

        # on different commands - answer in Telegram
        application.add_handler(CommandHandler("start", TelegramBot.start))
        application.add_handler(CommandHandler("help", TelegramBot.help_command))

        # on non command i.e message - echo the message on Telegram
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, TelegramBot.echo))

        # Run the bot until the user presses Ctrl-C
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    # Define a few command handlers. These usually take the two arguments update and
    # context.
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

    @staticmethod
    async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Echo the user message."""
        await update.message.reply_text(update.message.text)


if __name__ == "__main__":
    bot = TelegramBot()
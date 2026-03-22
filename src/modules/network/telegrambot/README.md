# TelegramBot Module Documentation

## Overview

The `TelegramBot` module is designed to interface with Telegram using the `python-telegram-bot` library. It provides functionalities to initialize the bot, handle commands, and publish messages to the application via a pub/sub mechanism. This documentation outlines the setup and usage of the `TelegramBot` class.

## Configuration

Before using the `TelegramBot` module, you need to configure it in the `config/telegram_bot.yml` file. Below is an explanation of the configuration options:

```yaml
telegram_bot:
  enabled: false  # Set to true to enable the TelegramBot module
  path: modules.network.telegrambot.TelegramBot  # Path to the TelegramBot class
  config:
    token: ''  # Telegram bot token (can also be set as an environment variable)
    user_whitelist: []  # List of user IDs allowed to interact with the bot
  dependencies:
    unix:
      - python3-pip
    python:
      - python-telegram-bot
```

### Dependencies

After enabling the module, run `./install.sh` to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

## Usage

### Initializing the TelegramBot

When the module is enabled in the config YAML, the `TelegramBot` class is automatically imported and initialized.

You can also reference the `TelegramBot` class directly in the `main.py`:

```python
module = module_instances['telegram_bot']  # Get the TelegramBot module instance
module.publish('telegram/respond', user_id=123456789, response="Hello, World!")  # Send a message to a user
```

### Setting Up the Bot

To set up the bot, follow these steps:

1. Search for BotFather in Telegram.
2. Start the BotFather.
3. Type `/newbot`.
4. Follow the instructions.
5. Copy the token (DON'T SHARE IT WITH ANYONE).
6. Create an environment variable called `TELEGRAM_BOT_TOKEN` and set it to the token (can also be set in the config YAML).
7. Run the script.

### Handling Commands

The `TelegramBot` class provides methods to handle commands and messages. Here’s an example of how to handle the `/start` and `/help` commands:

```python
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
```

### Publishing Messages

The `TelegramBot` class can publish messages to the application via a pub/sub mechanism. Here’s an example of how to publish a message:

```python
async def publish(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Publish the user's message to the application via pubsub."""
    user_id = update.effective_user.id
    message = update.message.text
    
    # Save the update for response handling
    self.update = update
    
    # Publish the message to other parts of the application
    self.publish('telegram/received', user_id=user_id, message=message)
    print(f"Published message from user {user_id}: {message} on topic telegram/received")
```

### Handling Responses

The `TelegramBot` class can handle responses from the application and send them back to the user. Here’s an example of how to handle a response:

```python
async def handle(self, user_id: int, response: str) -> None:
    """Handle responses from the application and send them back to the user."""
    if (user_id not in self.user_whitelist):
        print(f"User {user_id} not in whitelist, skipping response")
        return
    print(f"Handling response for user {user_id}: {response}")
    
    # Send the response back to the user on Telegram
    if self.update and self.update.effective_user.id == user_id:
        await self.update.message.reply_text(response)
```

## Conclusion

The `TelegramBot` module provides a straightforward interface for working with Telegram bots in Python. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and utilize the Telegram bot in your projects.
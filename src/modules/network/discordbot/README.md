# DiscordBot Module Documentation

## Overview

The `DiscordBot` module hosts a Discord bot that monitors for @mentions and
private messages, answers questions using the `ChatGPT` module, and returns
responses directly to Discord.

The bot responds to:

- **@mentions** in any server channel or thread.
- **Private messages (DMs)** — no @mention required.

When triggered the bot will:

1. Collect the recent thread history as context (if the message is already
   inside a thread).
2. Build a query from the thread context and the user's question.
3. Call `ai_instance.text_completion(query, persona=<system_prompt>)` where
   the system prompt contains the configured `prompt` text **plus the fetched
   text content** of every `knowledge_sources` URL (fetched once at startup).
4. Append the configured `footer` to the AI response (if set).
5. Post the response back to Discord:
   - **DM**: reply directly in the DM channel.
   - **Existing thread**: reply inside the thread.
   - **Regular channel**: create a new thread from the original message.

## Configuration

Enable the module by editing `config/discordbot.yml`:

```yaml
discordbot:
  enabled: true                               # Set to true to activate
  path: modules.network.discordbot.DiscordBot
  config:
    prompt: >
      You are a helpful assistant for the modular-biped open-source robotics
      project. Answer questions clearly and concisely, using the provided
      knowledge sources where relevant. If you are unsure of an answer, say so
      and direct the user to the appropriate knowledge source.
    # Maximum characters to extract from each knowledge source URL.
    max_chars_per_source: 5000
    # Footer appended to every AI response (Markdown supported).
    footer: |
      *I am a bot and currently in beta.*
      *Support the project: https://buymeacoffee.com/makerforgetech*
    knowledge_sources:
      - https://github.com/makerforgetech/modular-biped/wiki
      - https://github.com/makerforgetech/modular-biped/discussions
      - https://github.com/makerforgetech/modular-biped
  dependencies:
    python:
      - discord.py
    additional:
      - https://discord.com/developers/applications
```

### Configuration options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `prompt` | `str` | Built-in default | System prompt passed to the AI as the `persona` for every question. |
| `knowledge_sources` | `list[str]` | `[]` | URLs whose full text content is fetched at startup and embedded in the system prompt. |
| `max_chars_per_source` | `int` | `5000` | Maximum characters extracted from each knowledge-source URL. Increase for more context (higher token usage). |
| `footer` | `str` | `""` | Text appended to every AI response before posting. Markdown is supported. Leave empty to omit. |

## Dependencies

After enabling the module, install the required Python package:

```bash
pip install discord.py
```

Or run `./install.sh` if the project installer is configured to read module
dependencies.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | **Yes** | Discord bot token obtained from the Developer Portal. |

**Never commit your bot token to source control.**

## Setup

### 1. Create a Discord application and bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and give it a name.
3. Navigate to **Bot** → **Add Bot**.
4. Under **Token**, click **Reset Token** and copy the value.
5. Set the token as an environment variable:

   ```bash
   export DISCORD_BOT_TOKEN="your-token-here"
   ```

### 2. Configure bot permissions (intents)

In the Developer Portal under **Bot**:

* Enable **MESSAGE CONTENT INTENT** (required so the bot can read message text).

### 3. Invite the bot to your server

1. Navigate to **OAuth2 → URL Generator**.
2. Select the `bot` scope.
3. Under **Bot Permissions** select at minimum:
   - **Read Messages / View Channels**
   - **Send Messages**
   - **Create Public Threads**
   - **Send Messages in Threads**
4. Copy the generated URL and open it in a browser to invite the bot.

### 4. Wire up the ChatGPT module

The bot requires a `ChatGPT` module instance to be injected into
`DiscordBot.ai_instance` before it can answer questions. Set this in
`main.py` after both modules are loaded:

```python
discord_module.ai_instance = chatgpt_module
```

## Pubsub topics

### Topics the module subscribes to

| Topic | Arguments | Description |
|-------|-----------|-------------|
| `discord/send` | `channel_id` (int), `message` (str) | Allows other modules to post a message to a specific channel. |
| `system/exit` | – | Gracefully disconnects the bot when the system shuts down. |

### Topics the module publishes to

| Topic | Arguments | Description |
|-------|-----------|-------------|
| `log/*` | `message` (str) | Standard structured logging (via `BaseModule.log`). |

## Usage examples

### Asking the bot a question in a server channel

Simply @mention the bot followed by your question in any channel it can see:

```
@YourBot What is the purpose of the modular-biped project?
```

The bot will create a thread (or reply in the existing one) with an
AI-generated answer informed by the fetched knowledge-source content.

### Sending a private message

Message the bot directly — no @mention is required in a DM conversation.

### Sending a message from another module

```python
self.publish('discord/send', channel_id=123456789012345678, message='Hello from the robot!')
```

## Integration with the ChatGPT module

The `DiscordBot` module calls the `ChatGPT` module directly via
`ai_instance.text_completion()`:

```
@mention / DM → DiscordBot._on_message
  → ai_instance.text_completion(query, persona=system_prompt)
  → Discord thread / DM reply (with optional footer)
```

The system prompt (`persona`) contains the configured `prompt` text **plus
the full text content** of each `knowledge_sources` URL (fetched once at
startup using `urllib.request`).  HTML markup, navigation, scripts, and
styles are stripped so only meaningful article text reaches the model.

Both modules must be **enabled** in their respective YAML config files for
end-to-end functionality.

## Security

* The bot token is read exclusively from the `DISCORD_BOT_TOKEN` environment
  variable (or the optional `token` config key as a fallback). It is never
  logged or published over pubsub.
* Avoid storing the token in the config YAML file if the file is committed to
  source control.
* Knowledge-source URLs are fetched once at startup over HTTPS. Ensure URLs
  point to trusted, public resources.

## Conclusion

The `DiscordBot` module provides a Discord interface to the modular-biped AI
stack. By configuring a system prompt, a list of knowledge-source URLs (whose
content is automatically fetched and embedded at startup), and an optional
response footer, operators can deploy a bot that answers project-specific
questions in Discord channels and DMs with answers grounded in real project
documentation.

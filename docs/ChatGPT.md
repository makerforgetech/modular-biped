# ChatGPT Module Documentation

## Overview

The `ChatGPT` module is designed to interface with OpenAI's GPT models to provide conversational capabilities. It allows the robot to respond to speech inputs with text or predefined animations. This documentation outlines the setup and usage of the `ChatGPT` class.

## Configuration

Before using the `ChatGPT` module, you need to configure it in the `config/chatgpt.yml` file. Below is an explanation of the configuration options:

```yaml
chatgpt:
  enabled: false  # Set to true to enable the ChatGPT module
  path: 'modules.chatgpt.ChatGPT'  # Path to the ChatGPT class
  config:
    model: gpt-4o-mini  # Model to use for the chat
    persona: "You are a helpful assistant robot. You respond with short phrases where possible.
    Alternatively, you can respond with the following commands instead of text if you feel they are appropriate:
    - animate:head_nod
    - animate:head_shake"
  dependencies:
    python:
      - openai
    additional:
      - https://platform.openai.com/api-keys
```

### Dependencies

After enabling the module, run `./install.sh` to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

You must also obtain an API key from OpenAI to use the GPT models. The API key should be added as an environment variable  OPENAI_API_KEY:

```bash
export OPENAI_API_KEY="your-api-key"
```

Read here for config steps : https://platform.openai.com/docs/quickstart

## Usage

### Initializing the ChatGPT Module

When the module is enabled in the config YAML, the `ChatGPT` class is automatically imported and initialized.

### Chat Completion

The `completion` method sends the input text to the OpenAI API and processes the response. It can publish responses as text-to-speech (TTS) messages or trigger animations.

### Example Usage

You can test the `ChatGPT` module by running the following code:

```python
self.publish('speech', text='Hello, can you hear me?')
```

When the module is enabled in the config YAML, the `ChatGPT` class is automatically imported and initialized.

You can also reference the `ChatGPT` class directly in the main.py:

```python
module = module_instances['chatgpt'] 
module.completion('Can you hear me?')
```

## Customization

The `ChatGPT` module can be customized to meet specific requirements by modifying the persona, model, and response handling logic. You can update the configuration file to change the persona and model used for the chat.

## Conclusion

The `ChatGPT` module provides a powerful interface for adding conversational capabilities to the robot using OpenAI's GPT models. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and utilize the `ChatGPT` module in your projects.
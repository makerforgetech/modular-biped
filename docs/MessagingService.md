# Messaging Service Documentation

## Overview

The `MessagingService` module provides an abstraction layer for different messaging protocols, including `pypubsub` and `MQTT`. It allows modules to publish and subscribe to messages using a unified interface. This documentation outlines the setup and usage of the `MessagingService` class and explains how to create a new module that utilizes the `BaseModule` class, which includes a messaging service instance.

## Configuration

Before using the `MessagingService` module, you need to configure it in the `config/messaging_service.yml` file. Below is an explanation of the configuration options:

```yaml
messaging_service:
  enabled: true  # Set to true to enable the MessagingService module
  path: modules.network.messaging_service.MessagingService  # Path to the MessagingService class
  config:
    protocol: 'pubsub'  # Protocol to use ('pubsub' or 'mqtt')
    mqtt_host: 'localhost'  # MQTT broker host (if using MQTT)
    port: 1883  # MQTT broker port (if using MQTT)
  dependencies:
    python:
      - paho-mqtt
      - pypubsub
```

### Dependencies

After enabling the module, run `./install.sh` to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

## Usage

### Initializing the MessagingService

When the module is enabled in the config YAML, the `MessagingService` class is automatically imported and initialized.

You can also reference the `MessagingService` class directly in the `main.py`:

```python
module = module_instances['messaging_service']  # Get the MessagingService module instance
module.publish('system/log', message="Hello, World!")  # Publish a message
```

### Subscribing to Topics

The `MessagingService` class provides a method to subscribe to topics. Here’s an example of how to subscribe to a topic:

```python
def callback(message):
    print(message)

module.subscribe('system/log', callback)
```

### Publishing Messages

The `MessagingService` class provides a method to publish messages to topics. Here’s an example of how to publish a message:

```python
module.publish('system/log', message="Hello, World!")
```

## Creating a New Module

To create a new module that utilizes the `BaseModule` class, follow these steps:

1. Create a new Python file for your module (e.g., `my_module.py`).
2. Import the `BaseModule` class.
3. Define your module class and inherit from `BaseModule`.
4. Implement the necessary methods and messaging setup.

### Example: MyModule

```python
# filepath: /home/dan/projects/modular-biped/modules/my_module.py
from modules.base_module import BaseModule

class MyModule(BaseModule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = kwargs.get('value', 0)
        
        if kwargs.get('test_on_boot'):
            self.test()
            
    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('system/loop/1', self.loop)

    def loop(self):
        self.publish('my_module/value', value=self.value)

    def test(self):
        print(f"Initial value: {self.value}")
```

### Configuration for MyModule

Create a configuration file for your module (e.g., `config/my_module.yml`):

```yaml
my_module:
  enabled: true  # Set to true to enable the MyModule module
  path: modules.my_module.MyModule  # Path to the MyModule class
  config:
    value: 42  # Initial value
    test_on_boot: true  # Set to true to run a test on boot
```

### Using MyModule in main.py

Reference the `MyModule` class in the `main.py`:

```python
module = module_instances['my_module']  # Get the MyModule module instance
module.publish('my_module/value', value=100)  # Publish a value
```

## Conclusion

The `MessagingService` module provides a unified interface for different messaging protocols, making it easy to publish and subscribe to messages in your application. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and utilize the messaging service in your projects. Additionally, you can create new modules that inherit from the `BaseModule` class and leverage the messaging service for communication.
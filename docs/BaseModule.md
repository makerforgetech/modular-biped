# BaseModule Documentation

## Overview

The `BaseModule` class provides a foundational structure for all modules in the project. It includes essential functionalities such as messaging service integration, logging, and topic subscription. By extending this class, new modules can leverage these built-in features, ensuring consistency and reducing boilerplate code.

## Benefits of Extending BaseModule

1. **Unified Messaging Service**: The `BaseModule` class integrates with the `MessagingService`, allowing modules to publish and subscribe to messages using a unified interface.
2. **Consistent Logging**: The `log` method provides advanced logging capabilities, including class name, method name, and line number, ensuring consistent and informative log messages across all modules.
3. **Simplified Topic Subscription**: The `setup_messaging` method allows modules to define their own topic subscriptions, ensuring a standardized approach to message handling.
4. **Error Handling**: The class includes error handling for scenarios where the messaging service is not set, preventing runtime errors and ensuring robustness.

## Usage

### Initializing the BaseModule

To create a new module that extends the `BaseModule` class, follow these steps:

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

## Methods

### `messaging_service`

Getter and setter for the messaging service. Ensures that `setup_messaging` is called when the service is set.

```python
@property
def messaging_service(self):
    """Getter for messaging service."""
    return self._messaging_service

@messaging_service.setter
def messaging_service(self, service):
    """Setter for messaging service, ensures setup is called."""
    self._messaging_service = service
    self.setup_messaging()
```

### `setup_messaging`

Override this method in child classes to subscribe to topics.

```python
def setup_messaging(self):
    """Override this method in child classes to subscribe to topics."""
    pass  # No default implementation, subclasses should define their own subscriptions
```

### `publish`

Publish a message to a topic.

```python
def publish(self, topic, *args, **kwargs):
    if self.messaging_service is None:
        raise ValueError("Messaging service not set.")
    self.messaging_service.publish(topic, *args, **kwargs)
```

### `subscribe`

Subscribe to a topic.

```python
def subscribe(self, topic, callback, **kwargs):
    if self.messaging_service is None:
        raise ValueError("Messaging service not set.")
    self.messaging_service.subscribe(topic, callback, **kwargs)
```

### `log`

Advanced logging, includes class name, method name, and line number to message string.

```python
def log(self, message, level='info'):
    """
    Advanced logging, includes class name, method name, and line number to message string
    """
    # get class name, method name
    class_name = self.__class__.__name__
    method_name = inspect.stack()[1].function
    
    #get line number of calling class
    frame = inspect.stack()[1]

    message = f"[{class_name}.{method_name}:{frame.lineno}] {str(message)}"
    self.publish(f'log/{level}', message=message)
```

## Conclusion

The `BaseModule` class provides a robust foundation for creating new modules in the project. By extending this class, developers can leverage built-in messaging, logging, and subscription functionalities, ensuring consistency and reducing boilerplate code. This approach simplifies module development and enhances the maintainability of the project.
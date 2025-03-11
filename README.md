# Open Source, 3D Printable, Modular Bipedal Robot Project

The **Modular Bipedal Robot** project aims to educate and inspire individuals interested in robotics and electronics. This open-source initiative focuses on creating a fully autonomous companion robot with a variety of advanced features.

## Key Features

- **Bipedal Design**: The robot includes articulated legs for bipedal movement.
- **Control Systems**: Utilizes Arduino and Raspberry Pi, managed through custom PCBs.
- **Modular Body**: Configurable body components allow for easy customization and adaptability.
- **Software Modules**:
  - Animation: Handles the animation of the robot, including walking, turning, and other movements.
  - Braillespeak: Converts text to Braille and speaks it using a proprietary audio output using the onboard buzzer.
  - Buzzer: Controls the buzzer for audio output. Includes the ability to play tones and melodies.
  - ChatGPT: Uses the OpenAI GPT models to process text based on user input.
  - Logging: Logs data to a file for debugging and analysis.
  - Motion Detection: Handles motion detection using an onboard microwave motion sensor.
  - Neopixel: Controls the onboard Neopixel LEDs for visual feedback.
  - PiServo: Controls the servos connected to the Raspberry Pi.
  - PiTemperature: Reads the temperature from the integrated temperature sensor on the Raspberry Pi.
  - RTLSDR: Uses an RTL-SDR dongle to receive and process radio signals.
  - Serial Connection: Handles serial communication between the Raspberry Pi and Arduino.
  - Servos: Controls the servos connected to the Arduino via the Raspberry Pi and the serial connection.
  - Tracking: Uses computer vision to track objects and faces using the onboard camera.
  - Translator: Translates text between languages using the Google Translate API.
  - TTS: Converts text to speech using the onboard speaker.
  - Viam: Uses the VIAM API to integrate Viam modules for additional functionality.
  - Vision: Handles image processing and computer vision tasks using the onboard IMX500 Raspberry Pi AI camera.
  - Voice Recognition: Uses the Google Speech API to convert speech to text.
  - [Read more](https://github.com/makerforgetech/modular-biped/wiki/Software#modules)!

## Project Background

The Modular Biped Robot Project is designed to provide a flexible and modular framework for robotics development using Python and C++ on the Raspberry Pi and Arduino platforms. It aims to enable developers, robotics enthusiasts, and curious individuals to experiment, create, and customize their own biped robots. With a range of features and functionalities and the option to add your own easily, the Modular Biped Robot Project offers an exciting opportunity to explore the world of robotics.

## Modularity

The open source framework is designed for flexibility, allowing users to easily add or remove components to suit their specific needs. Comprehensive [guides](https://github.com/makerforgetech/modular-biped/wiki/Software#creating-a-module) are provided for integrating new modules seamlessly.

## Resources

- **Documentation**: For detailed information, visit the project’s GitHub wiki: [Modular Biped Documentation](https://github.com/makerforgetech/modular-biped/wiki)
- **Code**: Check out the modular open source software on [GitHub](https://github.com/makerforgetech/modular-biped)
- **YouTube Playlist**: Explore the development process through our build videos: [Watch on YouTube](https://www.youtube.com/watch?v=2DVJ5xxAuWY&list=PL_ua9QbuRTv6Kh8hiEXXVqywS8pklZraT)
- **Community**: Have a question or want to show off your build? Join the communities on [GitHub](https://bit.ly/maker-forge-community) and [Discord](https://bit.ly/makerforge-community)!


## A Note On Branches

The `main` branch is the latest stable release of the Modular Biped Robot project. This is compatible with the 'buddy' release, the latest supported release.

The `develop` branch is the development branch and may contain experimental features and changes that are not yet stable. Please use the `main` branch for the most stable experience. This will eventually become the next release, 'cody'. To facilitate testing modules are disabled by default in the `develop` branch. Enable each as needed in the config yaml files to test.

## Modules

The 'Cody' release includes a new BaseModule class that must be extended by all modules. This class provides a common interface for all modules to interact with the main robot controller. The BaseModule class includes a messaging_service object that references the main robot controller's messaging service. This object is used to send and receive messages between modules and the main robot controller.

Both `pypubsub` and `paho-mqtt` can be used to facilitate message passing between modules (mqtt support is not implemented yet). Which service is used can be set in the messaging_service configuration YAML file.

```yaml
messaging_service:
  enabled: true
  config:
    protocol: 'pubsub' # 'mqtt' or 'pubsub'
    mqtt_host: 'localhost' 
    mqtt_port: 1883
```

The introduction of mqtt allows distributed communication between modules, even across different devices.

The methods publish() and subscribe() can be utilised from within any module to send and receive messages to topics.

For example:
  
  ```python
  class MyModule(BaseModule):
    def __init__(self):
        # Don't subscribe here
        pass
    
    def setup_messaging(self):
        """Subscribe to necessary topics."""
        self.subscribe('my_topic', self.my_callback)
        
    def my_callback(self, message):
        print(f'Received message: {message}')
        self.publish('my_response_topic', 'Hello from MyModule!')
        self.log(level='info', message='MyModule received a message!')
  ```
Core and common topics include:
- `log` - Used for logging messages, accepts a string. or kwargs `type` (info by default) and `message`.
- `log/info` - Used for logging informational messages.
- `log/warning` - Used for logging warning messages.
- `log/error` - Used for logging error messages.
- `log/debug` - Used for logging debug messages.
- `log/critical` - Used for logging critical messages. 
- `system/loop` - The main loop event. Subscribe to this for an action to trigger every loop.
- `system/loop/1` - Triggers a loop every second.
- `system/loop/10` - Triggers a loop every 10 seconds.
- `system/loop/60` - Triggers a loop every 60 seconds.
- `system/loop/exit` - Triggers a loop exit event.
- `system/temperature` - The current temperature of the Pi.
- `motion` - Output from the motion sensor, only triggered if motion is detected.
- `speech` - Input from speech recognition module converted to text.
- `tts` - Output to be spoken by the TTS module.
- `animate` - Output to be animated by the Animation module.
- `vision/detections` - Output from the Vision module, containing detected objects.
- `led` - Output to the Neopixel LED module.

## Logging

An upgraded log manager has been included in this version. This allows logs to be published either via the above messaging service, or directly to a 'log' method within the BaseModule class. The log manager can be configured in the `logwrapper.yaml` file.

```yaml
logwrapper:
  enabled: true # Highly recommended to enable this module
  path: modules.logwrapper.LogWrapper
  config:
    filename: app.log
    log_level: 'debug' # debug, info, warning, error, critical
    cli_level: 'info' # debug, info, warning, error, critical
  dependencies:
    python:
      - pypubsub
```

Both the log level of the app.log file and the output to the CLI during runtime can be determined and defined separately. For any log level set, logs of a level equal to or above that level will be output. For example, if the log level is set to 'info', all logs of level 'info', 'warning', 'error', and 'critical' will be output.

Example usage:

```python
class MyModule(BaseModule):
    def my_method(self):
        self.log(level='info', message='MyModule has been initialised!')
        self.log(f"Current value: {value}")
        self.log(message=f"Current value is too high: {value}", level='critical')
```

In addition, for modules that extend BaseModule, the class, method and line number are prefixed to the message for output, making it easier to track down where the log was generated.

```
log/info: [Personality.random_neopixel_status:117] [Personality] Neopixel status triggered set to green
log/info: [PiTemperature.monitor:30] Temperature: 45.5°C
log/critical: [PiTemperature.monitor:28] Temperature is critical: 45.5°C
```

The app.log also includes timestamps and log levels for easy reference.

```
INFO: 01/30/2025 12:05:26 PM [Main] Loop started using pubsub protocol
INFO: 01/30/2025 12:05:27 PM [Personality.random_neopixel_status:117] [Personality] Neopixel status triggered set to green
INFO: 01/30/2025 12:05:27 PM [PiTemperature.monitor:30] Temperature: 42.2°C
INFO: 01/30/2025 12:05:28 PM [PiTemperature.monitor:30] Temperature: 42.2°C
INFO: 01/30/2025 12:05:28 PM [Main] Loop ended
```
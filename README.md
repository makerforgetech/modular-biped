# Open Source, 3D Printable, Modular Robot Project

The **Modular Robot** project aims to educate and inspire individuals interested in robotics and electronics. This open-source initiative focuses on creating a fully autonomous companion robot with a variety of advanced features.

## Key Features

- **Control Systems**: Utilizes Arduino and Raspberry Pi, managed through custom PCBs.
- **Modular Body**: Configurable body components allow for easy customization and adaptability.
- **Software Modules**:
  - Animation: Handles the animation of the robot, including walking, turning, and other movements. [README](src/modules/animate/README.md)
  - ArduinoSerial: Handles serial communication between the Raspberry Pi and Arduino. [README](src/modules/network/arduinoserial/README.md)
  - BNO055: Interfaces with the 9-DOF BNO055 IMU sensor over I2C for orientation and motion data. [README](src/modules/sensor/imu/bno055/README.md)
  - Braillespeak: Converts text to Braille and speaks it using a proprietary audio output using the onboard buzzer. [README](src/modules/audio/braillespeak/README.md)
  - BusServo: Controls serial bus servos (ST/SC series) with support for multiple backends (Waveshare, Rustypot, Simulation). [README](src/modules/actuators/bus_servo/README.md)
  - Buzzer: Controls the buzzer for audio output. Includes the ability to play tones and melodies. [README](src/modules/audio/buzzer/README.md)
  - ChatGPT: Uses the OpenAI GPT models to process text based on user input. [README](src/modules/chatgpt/README.md)
  - ControllerHandler: Maps gamepad inputs to robot actions using configurable YAML mappings, with modifier button support. [README](src/modules/controller_handler/README.md)
  - DiscordBot: Hosts a Discord bot that answers questions using ChatGPT, with configurable knowledge sources. [README](src/modules/network/discordbot/README.md)
  - Display (TFT): Controls a TFT display over SPI. [README](src/modules/display/tft_display_eye/README.md)
  - Display (OLED): Controls a Waveshare OLED display. [README](src/modules/display/waveshare_oled/README.md)
  - EmotionAnalysis: Maps text sentiment to NeoPixel LED colours. [README](src/modules/neopixel/emotion_analysis/README.md)
  - GPIO Laser: Controls a GPIO-connected laser. [README](src/modules/gpio/laser/README.md)
  - GPIO Read: General purpose GPIO input reader. [README](src/modules/gpio/read/README.md)
  - I2CServo: Controls servos connected via the I2C protocol. [README](src/modules/i2c_servo/README.md)
  - InputRecorder: Records and replays controller input events for creating animations. [README](src/modules/input_recorder/README.md)
  - Logging: Logs data to a file for debugging and analysis. [README](src/modules/logwrapper/README.md)
  - Motion Detection: Handles motion detection using an onboard microwave motion sensor. [README](src/modules/gpio/motion/README.md)
  - MPU6050: Interfaces with the MPU6050 accelerometer/gyroscope sensor over I2C. [README](src/modules/sensor/imu/mpu6050/README.md)
  - Neopixel: Controls the onboard Neopixel LEDs for visual feedback, supporting GPIO, I2C, and SPI protocols. [README](src/modules/neopixel/neopx/README.md)
  - Personality: Adds autonomous, reactive behaviours (animations, sounds, LED reactions) to the robot. [README](src/modules/personality/README.md)
  - PiServo: Controls the servos connected to the Raspberry Pi GPIO. [README](src/modules/actuators/piservo/README.md)
  - PiTemperature: Reads the CPU temperature from the Raspberry Pi and throttles the system when needed. [README](src/modules/pitemperature/README.md)
  - RTLSDR: Uses an RTL-SDR dongle to receive and process radio signals. [README](src/modules/network/rtlsdr/README.md)
  - Servo (Arduino): Controls servos connected to the Arduino via the Raspberry Pi serial connection. [README](src/modules/actuators/servo/README.md)
  - SpeechInput: Uses speech recognition to convert audio input to text. [README](src/modules/audio/speechinput/README.md)
  - TelegramBot: Enables remote control and interaction via a Telegram bot. [README](src/modules/network/telegrambot/README.md)
  - Tracking: Uses the IMX500 AI camera to track objects and faces. [README](src/modules/vision/imx500/tracking/README.md)
  - Translator: Translates text between languages using the Google Translate API. [README](src/modules/translator/README.md)
  - TTS: Converts text to speech using the onboard speaker. [README](src/modules/audio/ttsmodule/README.md)
  - Vision (IMX500): Object detection using the Raspberry Pi AI camera (IMX500). [README](src/modules/vision/imx500/vision/README.md)
  - Vision (OpenCV): Computer vision processing using OpenCV. [README](src/modules/vision/opencv/vision/README.md)
  - XboxController: Reads and normalises input from an Xbox-compatible gamepad. [README](src/modules/xbox_controller/README.md)
  - [Read more](https://github.com/makerforgetech/modular-biped/wiki/Software#modules)!

## Project Background

The Modular Robot Project is designed to provide a flexible and modular framework for robotics development using Python and C++ on the Raspberry Pi and Arduino platforms. It aims to enable developers, robotics enthusiasts, and curious individuals to experiment, create, and customize their own robots. With a range of features and functionalities and the option to add your own easily, the Modular Robot Project offers an exciting opportunity to explore the world of robotics.

## Modularity

The open source framework is designed for flexibility, allowing users to easily add or remove components to suit their specific needs. Comprehensive [guides](https://github.com/makerforgetech/modular-biped/wiki/Software#creating-a-module) are provided for integrating new modules seamlessly.

## Resources

- **Documentation**: For detailed information, visit the project's GitHub wiki: [Modular Robot Documentation](https://github.com/makerforgetech/modular-biped/wiki)
- **Code**: Check out the modular open source software on [GitHub](https://github.com/makerforgetech/modular-biped)
- **YouTube Playlist**: Explore the development process through our build videos: [Watch on YouTube](https://www.youtube.com/watch?v=2DVJ5xxAuWY&list=PL_ua9QbuRTv6Kh8hiEXXVqywS8pklZraT)
- **Community**: Have a question or want to show off your build? Join the communities on [GitHub](https://bit.ly/maker-forge-community) and [Discord](https://bit.ly/makerforge-community)!


## A Note On Branches

The `main` branch is the latest stable release of the Modular Robot project. This is compatible with the 'buddy' release, the latest supported release.

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

### The `loop()` Method

Modules that need to perform work on every system cycle should override the `loop()` method on `BaseModule`. The main loop calls `loop()` directly on each loaded module — no pub/sub subscription to `system/loop` is required.

```python
class MyModule(BaseModule):
    def loop(self):
        """Called every system loop cycle."""
        self.do_work()
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

### Servo Injection

Modules that need to control servos directly can request injection via the environment YAML:

```yaml
my_module:
  enabled: true
  inject:
    servos: "Servo_*"
```

This makes servo instances available as `self.servos['servo_name']` within the module, allowing direct method calls such as `self.servos['neck_tilt'].move(pitch)`.

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

# Getting Started

1. Clone the repository and navigate to the project directory.
2. Review the environment configuration files in the `environments` folder and create your own if needed.
3. Run install.sh <environment> to set up the necessary dependencies and configurations for your chosen environment.
4. Add any environment variables required to /home/$USER/.myenv (this file is sourced on startup to set environment variables for the session).
5. Test by running startup.sh to start the robot. You should see logs in the CLI and app.log file indicating that the robot is running.
6. Ctrl+C to stop the robot.
7. To enable autolaunch on boot, run `./installers/autolaunch.sh enable <environment>` (defaults to laptop if no environment specified). To disable autolaunch, run `./installers/autolaunch.sh disable`.

# Adding New Modules
To add a new module, create a new directory in the `src/modules` directory with the name of your module.

Inside this directory, create a Python file with the same name as the directory. This file should contain a class that extends the BaseModule class.

Implement the necessary methods and functionality for your module.

- `__init__(self, config, messaging_service)`: Initialize your module and set up any necessary variables or connections. The `config` parameter contains the configuration for your module from the YAML
- `setup_messaging(self)`: Set up any necessary subscriptions to topics using the `subscribe` method from the BaseModule class. You can subscribe to other topics or system/loop/<interval> for timed loops. See the wiki for more details on the messaging service and available topics.
- `loop(self)`: Implement the looping functionality of your module in this method. This method will be called directly on every main loop cycle — no pub/sub subscription needed. See the wiki for more details.
- `__exit__(self)`: Clean up any resources or connections when the module is stopped.

Create a configuration YAML file for your module in the new module's directory called `config.yml`. This file should include the class name of your module and any dependencies it requires, as well as any non-environment specific configuration.


```yaml
bno055:
  class: BNO055
  config:
    some_config: <this will be passed to the module's init method via kwargs>
  dependencies:
    python:
      - adafruit-circuitpython-bno055
      - adafruit-blinka
```

Finally, add your module to the configuration YAML file for your environment to enable it.

You may wish to include environment specific configuration in the environment YAML file, which will be passed to the module's init method via kwargs.

```yaml
bus_servo:
  enabled: true
  config:
    poses:
      - legs_forward: {leg_r_tilt: 2806, leg_r_hip: 1989, leg_r_knee: 1349, leg_r_ankle: 2754, neck_pan: 1698, neck_tilt: 118, leg_l_tilt: 1619, leg_l_hip: 1028, leg_l_knee: 2634, leg_l_ankle: 1567}
  instances:
    - name: leg_r_tilt
      model: ST3215
      id: 1
      range: [2511, 3944]
      range_degrees: 125.9
      start: 2810
    - name: leg_r_hip
      model: ST3215
      id: 3
      range: [0, 2063]
      range_degrees: 181.3
```

## Testing

All module tests can be run from the project root with:

```bash
bash test.sh
```

Individual test suites can also be targeted:

```bash
PYTHONPATH=src python3 -m unittest discover -s src/tests -p "test_*.py" -t src
PYTHONPATH=src python3 -m unittest discover -s src/modules -p "test_*.py" -t src
```

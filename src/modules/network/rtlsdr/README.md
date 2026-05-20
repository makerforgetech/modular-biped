# RTLSDR Module Documentation

## Overview

The `RTLSDR` module is designed to interface with RTL Software Defined Radio (SDR) using the `rtl_433` tool. It provides functionalities to start and stop the `rtl_433` process, listen to its HTTP streaming API, and handle JSON events. This documentation outlines the setup and usage of the `RTLSDR` class.

## Configuration

Before using the `RTLSDR` module, you need to configure it in the `config/rtlsdr.yml` file. Below is an explanation of the configuration options:

```yaml
rtlsdr:
  enabled: false  # Set to true to enable the RTLSDR module
  path: modules.network.rtlsdr.RTLSDR  # Path to the RTLSDR class
  config:
    udp_host: "127.0.0.1"  # Host for the UDP stream
    udp_port: 8433  # Port for the UDP stream
    timeout: 70  # Timeout for the HTTP connection
  dependencies:
    unix:
      - rtl-sdr
    python:
      - requests
```

### Dependencies

After enabling the module, run `./install.sh` to install the required dependencies. The dependencies are listed under `dependencies` in the configuration file. Check the output to ensure that the dependencies are installed correctly.

## Usage

### Initializing the RTLSDR

When the module is enabled in the config YAML, the `RTLSDR` class is automatically imported and initialized.

You can also reference the `RTLSDR` class directly in the `main.py`:

```python
module = module_instances['rtlsdr']  # Get the RTLSDR module instance
module.start_rtl_433()  # Start the rtl_433 process
module.listen_once()  # Listen to one chunk of the rtl_433 stream
```

### Starting and Stopping rtl_433

The `RTLSDR` class provides methods to start and stop the `rtl_433` process. Here’s an example of how to start and stop the process:

```python
module.start_rtl_433()  # Start the rtl_433 process
module.stop_rtl_433()  # Stop the rtl_433 process
```

### Listening to the Stream

The `RTLSDR` class provides methods to listen to the `rtl_433` HTTP stream and handle JSON events. Here’s an example of how to listen to the stream:

```python
module.listen_once()  # Listen to one chunk of the rtl_433 stream
module.rtl_433_listen()  # Listen to rtl_433 messages in a loop until stopped
```

### Handling Events

The `RTLSDR` class includes a method to handle JSON events from the `rtl_433` stream. Here’s an example of how to handle events:

```python
def handle_event(self, line):
    """Process each JSON line from rtl_433."""
    try:
        data = json.loads(line)
        print(data)
        self.publish('sdr/data', data=data)

        # Additional custom handling below
        # Example: print battery and temperature information
        label = data.get("model", "Unknown")
        if "channel" in data:
            label += ".CH" + str(data["channel"])
        elif "id" in data:
            label += ".ID" + str(data["id"])

        if data.get("battery_ok") == 0:
            print(f"{label} Battery empty!")
        if "temperature_C" in data:
            print(f"{label} Temperature: {data['temperature_C']}°C")
        if "humidity" in data:
            print(f"{label} Humidity: {data['humidity']}%")

    except json.JSONDecodeError:
        print("Failed to decode JSON line:", line)
```

## Conclusion

The `RTLSDR` module provides a straightforward interface for working with RTL Software Defined Radio (SDR) using the `rtl_433` tool. By following the configuration and usage instructions outlined in this documentation, you can effectively integrate and utilize the RTLSDR in your projects.
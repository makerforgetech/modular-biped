#!/usr/bin/env python3

import requests
import json
import subprocess
from time import sleep
from modules.base_module import BaseModule

class RTLSDR(BaseModule):
    def __init__(self, **kwargs):
        """
        RTL Software Defined Radio (SDR) class.
        Listen to the rtl_433's HTTP (line) streaming API of JSON events.
        
        Service must be started using `rtl_433 -F http` before listening. 
        This is handled with the start and stop methods.
        """
        self.udp_host = kwargs.get('udp_host', "127.0.0.1")
        self.udp_port = kwargs.get('udp_port', 8433)
        self.timeout = kwargs.get('timeout', 70)
        self.rtl_process = None  # Handle for the rtl_433 process
    
    def setup_messaging(self):
        self.subscribe('sdr/start', self.start_rtl_433)
        self.subscribe('sdr/listen', self.listen_once)
        self.subscribe('sdr/stop', self.stop_rtl_433)

    def start_rtl_433(self):
        """Starts the rtl_433 process with HTTP (line) streaming enabled."""
        if self.rtl_process is None:
            try:
                # Start the rtl_433 command
                self.rtl_process = subprocess.Popen(
                    ["rtl_433", "-F", f"http://{self.udp_host}:{self.udp_port}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"Started rtl_433 on {self.udp_host}:{self.udp_port}")
            except FileNotFoundError:
                print("rtl_433 command not found. Please ensure rtl_433 is installed.")
        else:
            print("rtl_433 is already running.")

    def stop_rtl_433(self):
        """Stops the rtl_433 process if it is running."""
        if self.rtl_process:
            self.rtl_process.terminate()
            self.rtl_process.wait()  # Ensure the process has completely exited
            self.rtl_process = None
            print("Stopped rtl_433 process.")
        else:
            print("rtl_433 is not currently running.")

    def stream_lines(self):
        """Stream lines from rtl_433's HTTP API."""
        url = f'http://{self.udp_host}:{self.udp_port}/stream'
        headers = {'Accept': 'application/json'}

        try:
            response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
            print(f'Connected to {url}')
            for chunk in response.iter_lines():
                yield chunk
        except requests.ConnectionError:
            print("Failed to connect to rtl_433 HTTP stream.")
            self.stop_rtl_433()

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

    def listen_once(self):
        """Listen to one chunk of the rtl_433 stream."""
        for chunk in self.stream_lines():
            chunk = chunk.rstrip()
            if chunk:
                self.handle_event(chunk)

    def rtl_433_listen(self):
        """Listen to rtl_433 messages in a loop until stopped."""
        self.start_rtl_433()
        try:
            while True:
                try:
                    self.listen_once()
                except requests.ConnectionError:
                    print("Connection failed, retrying in 5 seconds...")
                    sleep(5)
        finally:
            self.stop_rtl_433()

if __name__ == "__main__":
    try:
        sdr = RTLSDR()
        sdr.rtl_433_listen()
    except KeyboardInterrupt:
        print('\nExiting.')
        sdr.stop_rtl_433()

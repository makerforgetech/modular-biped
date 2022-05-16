[![Companion Robot](https://circleci.com/gh/danic85/companion-robot.svg?style=shield)](https://app.circleci.com/pipelines/github/danic85/companion-robot)

# Robotics Development Framework
This platform has been created to allow modular development and experimentation of robotics in python / C++ using the Raspberry Pi and Arduino.

## Installation
```
chmod 777 install.sh
./install.sh
```

Disable audio (see Neopixels section below)

## Running
```
./startup.sh
```
To execute manual control via keyboard:
```
./manual_startup.sh
```
To execute startup including a preview of the video feed (not available via SSH):
```
./preview_startup.sh
```

###Testing
```
python3 -m pytest --cov=modules --cov-report term-missing
```
## Features

### Facial detection and tracking
Using the Raspberry Pi camera

### Servo control
Control of up to 9 servos via an arduino serial connection

### Battery monitor
Both external and software integrated via the arduino serial connection

### Auto shutdown
Add the startup command to the boot file on the pi (edit `/etc/rc.local`)
This can then be stopped by running the `./stop.sh` command in the project directory.

GPIO 26 is also wired to allow shutdown when brought to ground via a switch.

Guide:
https://howchoo.com/g/mwnlytk3zmm/how-to-add-a-power-button-to-your-raspberry-pi

Script:

```
#!/usr/bin/env python

import RPi.GPIO as GPIO
import subprocess

GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.wait_for_edge(26, GPIO.FALLING)

subprocess.call(['pkill', '-f', 'main.py'], shell=False) # kill main script safely
subprocess.call(['shutdown', '-h', 'now'], shell=False)
```

### Buzzer
A buzzer is connected to GPIO 27 to allow for tones to be played in absence of audio output (see Neopixel below).
https://github.com/gumslone/raspi_buzzer_player.git

### Motion Sensor
An RCWL-0516 microwave radar sensor is equipped on GPIO 13

### Stereo MEMS Mics
GPIO 18, 19 and 20 allow stereo MEMS microphones as audio input
```
Mic 3V to Pi 3.3V
Mic GND to Pi GND
Mic SEL to Pi GND (this is used for channel selection, connect to either 3.3V or GND)
Mic BCLK to BCM 18 (pin 12)
Mic DOUT to BCM 20 (pin 38)
Mic LRCL to BCM 19 (pin 35)
```
https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test


```
cd ~
sudo pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/i2smic.py
sudo python3 i2smic.py
```

####Test
`arecord -l`
`arecord -D plughw:0 -c2 -r 48000 -f S32_LE -t wav -V stereo -v file_stereo.wav`

_Note:_ See below for additional configuration to support voice recognition

### Speech Recognition
Trigger word for voice recognition (currently not used):
https://snowboy.kitt.ai/

Speech recognition is enabled whenever a face is visible. 
Ensure that the `device_index` specified in `modules/speechinput.py` matches your microphone. 

See `scripts/speech.py` to list input devices and test. See below for MEMS microphone configuration

### MEMS Microphone configuration for speech recognition

By default the Adafruit I2S MEMS Microphone Breakout does not work with speech recognition. 

To support voice recognition on the MEMS microphone(s) the following configuration changes are needed.

`sudo apt-get install ladspa-sdk`

Create `/etc/asound.conf` with the following content:

``` 
pcm.pluglp {
    type ladspa
    slave.pcm "plughw:0"
    path "/usr/lib/ladspa"
    capture_plugins [
   {   
      label hpf
      id 1042
   }
        {
                label amp_mono
                id 1048
                input {
                    controls [ 30 ]
                }
        }
    ]
}

pcm.lp {
    type plug
    slave.pcm pluglp
}
```

This enables the device 'lp' to be referenced in voice recognition. Shown with index `18` in the example below.

Sample rate should also be set to `16000`

`mic = sr.Microphone(device_index=18, sample_rate=16000)`

References: 

* [MEMS Microphone Installation Guide](https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test)

* [Adafruit Support discussing issue](https://forums.adafruit.com/viewtopic.php?f=50&t=181675&p=883853&hilit=MEMS#p883853)

* [Referenced documentation of fix](https://github.com/mpromonet/v4l2rtspserver/issues/94)

### Serial communication with Arduino

In order to use the Raspberry Pi’s serial port, we need to disable getty (the program that displays login screen)

`sudo raspi-config ->  Interfacing Options -> Serial -> "Would you like a login shell to be accessible over serial" = 'No'. Restart`

#### Connection via serial pins
Connect the Pi GPIO 14 & 15 (tx & rx) to the arduino tx & rx (tx -> rx in both directions!) via a logic level shifter, as the Pi is 3v3 and the arduino is (most likely) 5v.

####Upload to Arduino over serial pins
To upload over serial pins, press the reset button on the Arduino at the point that the IDE starts 'uploading' (after compile), otherwise a sync error will display.

### Neopixel

WS1820B support is included via the Pi GPIO pin 12. Unfortunately to support this you must disable audio on the Pi.

```
sudo vim /boot/config.txt
#dtparam=audio=on
```

This is also why the application must be executed with `sudo`

https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage

## PCBs
Prefabricated PCBs are available for this project in the `circuits` folder. This allows the connection between the core components as described above.

![Top](circuits/v2/Upper/Top%20Feb%202021_pcb.png)

![Bottom](circuits/v2/Lower/Lower%20Feb%202021_pcb.png)

# really-useful-robot
Robot development platform

**Overview**

This project contains modules to enable serial communication between a Pi 3 and an arduino nano to facilitate the movement of servos, display of addressable LEDs, and output of sound.

Each module enables different functionality, in varying states of completion.

This is a WIP project that will be released when v1.0 is stable. Until then feel free to make use of the modules in isolation, or use this as a basis for a robotics platform.

**Get Started**

Run install.sh on a Raspberry Pi

To run, execute startup.sh

Trigger word for voice recognition:
https://snowboy.kitt.ai/

In order to use the Raspberry Pi’s serial port, we need to disable getty (the program that displays login screen)

`sudo raspi-config ->  Interfacing Options -> Serial -> "Would you like a login shell to be accessible over serial" = 'No'. Restart`

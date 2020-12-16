# Robotics Development Environment
This platform has been created to allow modular development and experimentation of robotics in python / C++ using the Raspberry Pi and Arduino.


###Voice Recognition
Trigger word for voice recognition:
https://snowboy.kitt.ai/

### Serial communication with Arduino

In order to use the Raspberry Pi’s serial port, we need to disable getty (the program that displays login screen)

`sudo raspi-config ->  Interfacing Options -> Serial -> "Would you like a login shell to be accessible over serial" = 'No'. Restart`

###Upload to Arduino over serial pins
To upload over serial pins, press the reset button on the Arduino at the point that the IDE starts 'uploading' (after compile), otherwise a sync error will display.
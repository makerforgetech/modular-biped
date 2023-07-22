sudo pkill -f /home/archie/companion-robot/main.py
sudo pkill -f /home/archie/companion-robot/RFID.py
sudo modprobe bcm2835-v4l2 # Enable camera
sudo pigpiod # GPIO @todo may not be used
sudo python2 /home/archie/companion-robot/RFID.py

#!/bin/bash
# Define the username as a variable (replace "archie" with the actual username)
username="archie"

# Check if the user is logged in
if who | grep -wq "$username"; then
  # If the user is logged in, start the desired file here
  echo "User is logged in, running the file..."
  sudo python3 /home/archie/companion-robot/main.py preview
else
  # If the user is not logged in, print a message
  echo "User is not logged in, the file won't be executed."
fi

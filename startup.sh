#!/bin/bash

# Force release of audio devices, fixes "Device or resource busy" error on amplifier
sudo fuser -k /dev/snd/*

# Set the base directory to the location of this script
BASE_DIR="$(dirname "$(realpath "$0")")"

# Ensure any existing instance of main.py is terminated
sudo pkill -f "$BASE_DIR/main.py"

# Source /home/$USER/.myenv to set environment variables for this session
if [ -f "/home/$USER/.myenv" ]; then
    echo "Sourcing environment variables from /home/$USER/.myenv"
    set -a # Automatically export all variables
    source "/home/$USER/.myenv"
    set +a # Disable automatic export
else
    echo "No environment file found at /home/$USER/.myenv. Continuing without sourcing environment variables."
fi

# Start necessary services
# sudo modprobe bcm2835-v4l2 # Enable camera (if needed)
sudo pigpiod # Start the GPIO daemon.

# If mac
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS specific commands (if any)
  echo "Running on macOS"
  brew services start mosquitto
else
  # Linux specific commands
  echo "Running on Linux"
  sudo systemctl start mosquitto
fi

# Accept an optional environment argument and pass as --env (default to no argument, main.py defaults to 'robot')
if [ -n "$1" ]; then
	ENV_ARG="--env $1"
else
	ENV_ARG=""
fi
"$BASE_DIR/myenv/bin/python3" "$BASE_DIR/src/main.py" $ENV_ARG


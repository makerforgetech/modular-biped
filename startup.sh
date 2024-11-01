#!/bin/bash

# Set the base directory to the location of this script
BASE_DIR="$(dirname "$(realpath "$0")")"

# Ensure any existing instance of main.py is terminated
sudo pkill -f "$BASE_DIR/main.py"

# Start necessary services
# sudo modprobe bcm2835-v4l2 # Enable camera (if needed)
sudo pigpiod # Start the GPIO daemon

# Run main.py using the virtual environment's Python interpreter
"$BASE_DIR/myenv/bin/python3" "$BASE_DIR/main.py"

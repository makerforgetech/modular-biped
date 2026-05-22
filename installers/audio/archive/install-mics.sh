#!/bin/bash

INSTALL_FLAG="$(dirname "$0")/i2s_mic_installed.flag"

# Function to check if the script is running as root
require_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root. Exiting."
    exit 1
  fi
}

# Function to clear the terminal
clear_terminal() {
  clear
}

# Function to detect Raspberry Pi model
detect_pi_model() {
  if ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Non-Raspberry Pi board detected. Exiting."
    exit 1
  fi

  local model=$(cat /proc/device-tree/model)
  echo "$model"
}

# Function to prompt the user with a yes/no question
prompt_yes_no() {
  local prompt="$1"
  while true; do
    read -p "$prompt [y/n]: " yn
    case $yn in
      [Yy]* ) return 0;;
      [Nn]* ) return 1;;
      * ) echo "Please answer yes or no.";;
    esac
  done
}

# Function to write to a file
write_text_file() {
  local file="$1"
  local content="$2"
  echo "$content" > "$file"
}

# Set up Python virtual environment if needed
setup_python_env() {
  local venv_dir="$(dirname "$0")/myenv"
  if [[ ! -d "$venv_dir" ]]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$venv_dir"
  fi
  echo "Activating Python virtual environment..."
  source "$venv_dir/bin/activate"
}

# Check if the script has already been run
if [[ -f $INSTALL_FLAG ]]; then
  echo "I2S microphone support has already been installed. Exiting."
  echo "Test with 'arecord -D plughw:2 -c2 -r 48000 -f S32_LE -t wav -V stereo -v file_stereo.wav' where plughw: is the card number shown with 'arecord -l'"
  exit 0
fi

# Main script
require_root
clear_terminal

cat << EOF
This script downloads and installs
I2S microphone support.
EOF

CONFIG_FILE="/boot/firmware/config.txt"
LINE="dtoverlay=googlevoicehat-soundcard"

# Check if the line already exists
if grep -Fxq "$LINE" "$CONFIG_FILE"; then
    echo "The line '$LINE' already exists in $CONFIG_FILE."
else
    # Append the line to the file
    echo "$LINE" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "The line '$LINE' has been added to $CONFIG_FILE."
fi

pi_model=$(detect_pi_model)
echo "$pi_model detected.\n"

case "$pi_model" in
  *"Raspberry Pi Zero"*)
    pimodel_select=0
    ;;
  *"Raspberry Pi 2 Model B"*|*"Raspberry Pi 3"*|*"Raspberry Pi Zero 2"*)
    pimodel_select=1
    ;;
  *"Raspberry Pi 4"*|*"Raspberry Pi Compute Module 4"*|*"Raspberry Pi 400"*|*"Raspberry Pi Compute Module 5"*|*"Raspberry Pi 5"*)
    pimodel_select=2
    ;;
  *)
    echo "Unsupported Pi board detected. Exiting."
    exit 1
    ;;
esac

if prompt_yes_no "Auto load module at boot?"; then
  auto_load=true
else
  auto_load=false
fi

cat << EOF
Installing...
EOF

# Set up Python environment
setup_python_env

# Install required packages
apt-get -y install git raspberrypi-kernel-headers

# Clone the repository
# git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git

# Build and install the module
# cd Raspberry-Pi-Installer-Scripts/i2s_mic_module || exit
# make clean
# make
# make install

# Set up auto load at boot if selected
if $auto_load; then
  write_text_file /etc/modules-load.d/snd-i2smic-rpi.conf "snd-i2smic-rpi"
  write_text_file /etc/modprobe.d/snd-i2smic-rpi.conf "options snd-i2smic-rpi rpi_platform_generation=$pimodel_select"
fi

# Enable I2S overlay
if [[ -f /boot/firmware/config.txt ]]; then
  sed -i -e 's/#dtparam=i2s/dtparam=i2s/g' /boot/firmware/config.txt
else
  sed -i -e 's/#dtparam=i2s/dtparam=i2s/g' /boot/config.txt
fi

# Create the install flag file to prevent reinstallation
touch $INSTALL_FLAG

cat << EOF
DONE.

Settings take effect on next boot.
EOF

if prompt_yes_no "Reboot now?"; then
  reboot
fi

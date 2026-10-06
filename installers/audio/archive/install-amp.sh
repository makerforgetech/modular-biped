#!/bin/bash

set -e

# Variables
BLACKLIST="/etc/modprobe.d/raspi-blacklist.conf"
PRODUCT_NAME="I2S Amplifier"
FLAG_FILE="i2s_amp_installed.flag"
CONFIG="/boot/config.txt"
ALT_CONFIG="/boot/firmware/config.txt"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt user
prompt() {
    read -p "$1 [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to check if running on Raspberry Pi
is_raspberry_pi() {
    if [ -f /proc/device-tree/model ]; then
        grep -q "Raspberry Pi" /proc/device-tree/model
    else
        return 1
    fi
}

# Function to check if driver is loaded
driver_loaded() {
    lsmod | grep -q "$1"
}

# Function to write a file
write_file() {
    echo -e "$2" > "$1"
}

# Function to append to asound.conf without overwriting existing settings
append_to_asound_conf() {
    local CONFIG_CONTENT="$1"
    local IDENTIFIER="$2"

    if grep -q "$IDENTIFIER" /etc/asound.conf 2>/dev/null; then
        echo "$IDENTIFIER already exists in /etc/asound.conf. Skipping."
    else
        echo -e "$CONFIG_CONTENT" >> /etc/asound.conf
        echo "$IDENTIFIER added to /etc/asound.conf."
    fi
}

# Check for root permissions
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root."
    exit 1
fi

# Check for installer flag
if [ -f "$FLAG_FILE" ]; then
    echo "Installer has already been run. Exiting."
    exit 0
fi

# Check for prerequisite installer flags
if [ ! -f "i2s_speech_recognition_installed.flag" ]; then
    echo "Error: i2s_speech_recognition_installed.flag not found in the current directory."
    echo "Ensure that the I2S Speech Recognition setup is installed before running this script."
    exit 1
fi

if [ ! -f "i2s_mic_installed.flag" ]; then
    echo "Error: i2s_mic_installed.flag not found in the current directory."
    echo "Ensure that the I2S Microphone setup is installed before running this script."
    exit 1
fi

# Ensure running on Raspberry Pi
if ! is_raspberry_pi; then
    echo "Non-Raspberry Pi board detected. Exiting."
    exit 1
fi

# Welcome message
echo -e "\nThis script will install everything needed to use\n$PRODUCT_NAME.\n"
echo -e "--- Warning ---\n\nAlways be careful when running scripts and commands\ncopied from the internet. Ensure they are from a\ntrusted source.\n"
if ! prompt "Do you wish to continue?"; then
    echo "Aborting..."
    exit 0
fi

# Determine config file
if [ -f "$ALT_CONFIG" ]; then
    CONFIG="$ALT_CONFIG"
fi

if [ ! -f "$CONFIG" ]; then
    echo "No Device Tree detected. Not supported."
    exit 1
fi

# Add Device Tree Entry
# echo -e "\nAdding Device Tree Entry to $CONFIG"
# if grep -q "^dtoverlay=max98357a" "$CONFIG"; then
#     echo "dtoverlay already active."
# else
#     echo "dtoverlay=max98357a" >> "$CONFIG"
#     REBOOT=true
# fi

# Update blacklist if it exists
if [ -f "$BLACKLIST" ]; then
    echo -e "\nCommenting out Blacklist entry in $BLACKLIST"
    sed -i.bak \
        -e '/^blacklist[[:space:]]*snd_soc_max98357a/s/^/\#/g' \
        -e '/^blacklist[[:space:]]*snd_soc_max98357a_i2c/s/^/\#/g' "$BLACKLIST"
fi

# Configure sound output
echo "Configuring sound output"

# Backup existing asound.conf if not already backed up
if [ -f "/etc/asound.conf" ] && [ ! -f "/etc/asound.conf.amp.bak" ]; then
    cp /etc/asound.conf /etc/asound.conf.bak
    echo "Backup of /etc/asound.conf created at /etc/asound.conf.amp.bak"
fi

# Append amplifier configuration
AMP_CONF="""
# I2S Amplifier Configuration
pcm.speakerbonnet {
   type hw card 0
}

pcm.dmixer {
   type dmix
   ipc_key 1024
   ipc_perm 0666
   slave {
     pcm "speakerbonnet"
     period_time 0
     period_size 1024
     buffer_size 8192
     rate 44100
     channels 2
   }
}

ctl.dmixer {
    type hw card 0
}

pcm.softvol {
    type softvol
    slave.pcm "dmixer"
    control.name "PCM"
    control.card 0
}

ctl.softvol {
    type hw card 0
}

pcm.amplifier {
    type plug
    slave.pcm "softvol"
}
"""

append_to_asound_conf "$AMP_CONF" "# I2S Amplifier Configuration"

# Install aplay systemd service
echo "Installing aplay systemd unit"
write_file /etc/systemd/system/aplay.service "[Unit]
Description=Invoke aplay from /dev/zero at system start.

[Service]
ExecStart=/usr/bin/aplay -D default -t raw -r 44100 -c 2 -f S16_LE /dev/zero

[Install]
WantedBy=multi-user.target"

systemctl daemon-reload
systemctl disable aplay

if prompt "Activate '/dev/zero' playback in background? [RECOMMENDED]"; then
    systemctl enable aplay
    REBOOT=true
fi

# Test driver and sound
if driver_loaded "max98357a"; then
    echo -e "\nWe can now test your $PRODUCT_NAME"
    echo "Set your speakers at a low volume if possible!"
    if prompt "Do you wish to test your system now?"; then
        echo "Testing... If you have issues please restart and try again. Use 'aplay -l' to check the card number (defaults here to 0)."
        speaker-test -l5 -c2 -t wav -D plughw:0
    fi
fi

# Final message
echo -e "\nAll done! Enjoy your new $PRODUCT_NAME!"
if [ "$REBOOT" = true ]; then
    echo "A reboot is required to apply changes. Then run this script again."
    if prompt "Reboot now?"; then
        reboot
    fi
fi



# Create installer flag file
# touch "$FLAG_FILE" # not needed

#!/bin/bash

# This script sets up speech recognition configuration for a Raspberry Pi.
# It creates and modifies the /etc/asound.conf file and sets default audio devices.

# Check if the script has already been installed
if [ -f "i2s_speech_recognition_installed.flag" ]; then
    echo "Speech recognition setup is already installed. Exiting."
    exit 0
fi

# Check for the presence of the i2s_mic_installed.flag file
if [ ! -f "i2s_mic_installed.flag" ]; then
    echo "Error: i2s_mic_installed.flag not found in the current directory. Please run 'install-mics.sh' first to set up the microphones."
    exit 1
fi

# Function to detect the card index for the microphone
detect_microphone() {
    echo "Detecting available audio devices..."
    arecord -l

    echo "\nPlease enter the card index for your microphone from the list above:"
    read -r mic_index

    echo "\nUsing card index: $mic_index"
    echo
    return $mic_index
}

# Prompt for microphone index
detect_microphone
mic_index=$?

# Backup the existing /etc/asound.conf file if it exists
if [ -f "/etc/asound.conf" ]; then
    sudo cp /etc/asound.conf /etc/asound.conf.bak
    echo "Backup of /etc/asound.conf created at /etc/asound.conf.bak"
fi

# Create /etc/asound.conf with the required content
sudo bash -c "cat > /etc/asound.conf" <<EOL
pcm.pluglp {
    type ladspa
    slave.pcm "plughw:$mic_index"
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

pcm.!default {
    type plug
    slave.pcm "pluglp"
}
EOL

# Display the new /etc/asound.conf file
echo "\n/etc/asound.conf has been configured with the following content:"
cat /etc/asound.conf

# Create the installation flag file
touch i2s_speech_recognition_installed.flag

# Inform the user about restarting audio services
echo "\nConfiguration complete. Please restart your Raspberry Pi or audio services for changes to take effect."
echo "\nEnsure your speech recognition script uses the following parameters:"
echo "\nmic = sr.Microphone(device_index=18, sample_rate=16000)"
echo "\nThis sets the sample rate to 16000 and uses the configured device."

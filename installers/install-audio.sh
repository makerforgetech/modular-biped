mkdir audio/backups/backup-$(date +%Y-%m-%d-%H-%M-%S)
cd audio/backups/backup-$(date +%Y-%m-%d-%H-%M-%S)
cp /boot/firmware/config.txt config.txt
cp /etc/modprobe.d/raspi-blacklist.conf raspi-blacklist.conf
cp /etc/asound.conf asound.conf
cp /etc/systemd/system/aplay.service aplay.service

echo "Backed up current audio configuration files to $(pwd)."
echo "Installing audio config."
cd ../../..

# Compile and install the custom cm5-i2s-audio device tree overlay.
# This overlay creates a simple-audio-card with proper DAPM routes for both
# the MAX98357A speaker (device 1) and ICS-43434 stereo mics (device 0).
echo "Compiling cm5-i2s-audio device tree overlay..."
if ! command -v dtc &> /dev/null; then
    echo "dtc not found — installing device-tree-compiler..."
    sudo apt-get install -y device-tree-compiler
fi
dtc -@ -I dts -O dtb -o /tmp/cm5-i2s-audio.dtbo audio/cm5-i2s-audio.dts
sudo cp /tmp/cm5-i2s-audio.dtbo /boot/firmware/overlays/cm5-i2s-audio.dtbo
echo "cm5-i2s-audio.dtbo installed to /boot/firmware/overlays/"

sudo cp audio/config.txt /boot/firmware/config.txt
sudo cp audio/raspi-blacklist.conf /etc/modprobe.d/raspi-blacklist.conf
sudo cp audio/asound.conf /etc/asound.conf
sudo cp audio/aplay.service /etc/systemd/system/aplay.service

# Disable aplay.service: it holds the hardware open via ALSA dmix, which
# blocks PipeWire (the default audio server on Bookworm) from accessing the
# device. PipeWire handles device lifecycle and mixing natively.
sudo systemctl disable --now aplay.service 2>/dev/null || true

echo "Audio configuration files copied. Please reboot the system for changes to take effect."


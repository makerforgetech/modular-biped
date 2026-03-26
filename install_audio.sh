
sudo python3 -m pip install --upgrade click --break-system-packages

sudo python3 -m pip install --upgrade setuptools --break-system-packages
sudo python3 -m pip install --upgrade adafruit-python-shell --break-system-packages

sudo python3 installers/i2samp.py

# Example aplay -l output on CM5 before googlevoicehat overlay takes effect (first boot after install):
# card 0: vc4hdmi0 [vc4-hdmi-0], device 0: MAI PCM i2s-hifi-0 [MAI PCM i2s-hifi-0]
# card 1: vc4hdmi1 [vc4-hdmi-1], device 0: MAI PCM i2s-hifi-0 [MAI PCM i2s-hifi-0]
# card 2: I2S [Dual I2S], device 0: 1f000a0000.i2s-dit-hifi dit-hifi-0 [...]
#
# After reboot with googlevoicehat overlay active - card numbers can vary between boots!
# card 0: vc4hdmi0 [vc4-hdmi-0], ...
# card 1: vc4hdmi1 [vc4-hdmi-1], ...
# card 2: sndrpigooglevoi [snd_rpi_googlevoicehat_soundcar], device 0: Google voiceHAT SoundCard HiFi ...
#   OR (on a subsequent restart):
# card 1: sndrpigooglevoi [snd_rpi_googlevoicehat_soundcar], device 0: Google voiceHAT SoundCard HiFi ...
# card 2: vc4hdmi1 [vc4-hdmi-1], ...
#
# This is why asound.conf must reference the card by NAME (sndrpigooglevoi) not by number.

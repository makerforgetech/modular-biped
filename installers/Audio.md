# I2S Audio Configuration Summary (Reference)

All the configuration is based on two scripts from Adafruit, which in turn were based on scripts from Pimoroni.
https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/

- i2samp.py : Installer script for I2S audio devices.
- i2smic.py : Installer script for I2S microphone devices.

In addition, there is configuration needed to allow speech recognition to work with the microphone.

The Adafruit scripts were recently moved from shell scripts to Python scripts, however I also have my own shell scripts in the `installers/` folder which are based on their original shell scripts.

In 2025 I had to configure audio on the CM5 carrier board. This was partially successful but I needed to restart and occasionally re-run the i2samp.py script to get audio working again.

As far as I know there are no differences between the Raspberry Pi 5 and CM5 in terms of audio configuration.

Unfortunately, when testing recently I can't get this to work at all on the CM5. The devices are detected but I have not managed to get them to record or play audio.

Below is the dump of my investigation around the configuration files needed, and the ideal contents of those files. Despite this I have not managed to resolve the issues on the CM5.

## Root Cause Analysis (CM5 Audio Not Working)

The following issues were identified as likely root causes for audio not working on the CM5:

### Issue 1 — ALSA card number is hardcoded to 0 in `asound.conf` (Critical)

`asound.conf` referenced `card 0` everywhere. On CM5, the two vc4-hdmi devices
enumerate first (as cards 0 and 1), so the I2S soundcard ends up as **card 1 or
card 2** — and the actual card number changes between boots depending on
enumeration order. This means ALSA's softvol/dmix chain was targeting the wrong
device (an HDMI output), not the MAX98357B.

**Fix applied:** All `card 0` references in `asound.conf` are replaced with
`card sndrpigooglevoi` (the stable ALSA name of the googlevoicehat card),
so the configuration always targets the correct device regardless of enumeration
order.

> **Note:** `hdmi_ignore_edid_audio=1` prevents HDMI from being auto-selected
> as the *default* audio device, but it does **not** prevent the vc4hdmi cards
> from appearing with low card numbers in `aplay -l`.

### Issue 2 — No capture (microphone) path defined in `asound.conf`

The previous `asound.conf` defined `pcm.!default` as `type plug → softvol →
dmix`, which is a **playback-only** chain. Running `arecord -D default` or any
speech-recognition library against the default device would fail because
`dmix` cannot be used for capture.

**Fix applied:** `pcm.!default` is changed to `type asym`, which independently
routes:
- Playback → softvol → dmix → I2S card (unchanged)
- Capture → `hw:sndrpigooglevoi` (direct hardware access to the I2S mic)

### Issue 3 — `i2smic.py` bails on CM5 / Pi 5

The Adafruit `i2smic.py` script builds and installs the custom `snd-i2smic-rpi`
kernel module for I2S PDM microphones. The model-detection table only listed Pi
models up to Pi 4 / CM4. Running the script on a CM5 caused it to exit with
*"Unsupported Pi board detected."*, meaning the kernel module was **never
installed**.

**Fix applied:** CM5 and Pi 5 model strings (`RASPBERRY_PI_5B`,
`RASPBERRY_PI_CM5`, `RASPBERRY_PI_5`) are added to the model table with
`pimodel_select = 2` (same platform generation as Pi 4 / CM4).

> **Note:** The `googlevoicehat-soundcard` overlay itself exposes a capture
> device for I2S microphones connected to the Pi's I2S DATA-IN pin. If that
> capture device works correctly for the ICS-43434, running `i2smic.py` may
> not be necessary. Use `arecord -l` to verify which capture devices appear
> after reboot.

### Issue 4 — `install_audio.sh` and `i2samp.py` contained unresolved merge conflict markers

Both files had `<<<<<<< / ======= / >>>>>>>` conflict markers committed into the
branch. This would cause Python syntax errors and shell script failures at
runtime.

**Fix applied:** Conflicts resolved — the system-Python3 / `--break-system-packages`
variant of `install_audio.sh` is kept (appropriate for Raspberry Pi OS Bookworm),
and the correct f-string `print(f"\nEnjoy your new {PRODUCT_NAME}!")` is kept
in `i2samp.py`.

---

## 1. Device Tree and Overlays
- Only one I2S audio overlay should be enabled in `/boot/firmware/config.txt` (or `/boot/config.txt`).
- For the Google Voice HAT, use:
	```
	dtoverlay=googlevoicehat-soundcard
	```
- Disable onboard audio to avoid conflicts:
	```
	#dtparam=audio=on
	```
- To prevent HDMI audio devices from appearing and changing card numbers, add:
	```
	hdmi_ignore_edid_audio=1
	```
- Comment out or remove any other I2S overlays (e.g., `max98357a`, `dual_i2s`, `i2s-mmap`).

**Example [all] section:**
```
[all]
dtparam=uart0=on
dtoverlay=googlevoicehat-soundcard
hdmi_ignore_edid_audio=1
#dtparam=audio=on # this may be added elsewhere; ensure it's disabled
```

## 2. Blacklist File
- `/etc/modprobe.d/raspi-blacklist.conf` is usually empty or does not exist by default.
- If present, ensure any lines blacklisting I2S drivers are commented out (start with `#`).

## 3. ALSA Configuration (`/etc/asound.conf`)
- This file defines the software audio pipeline for playback **and capture**.
- Reference the card by **name** (`sndrpigooglevoi`), not by number. The card
  number changes between boots on CM5/Pi 5 because the two vc4-hdmi devices
  are enumerated first.
- Use `type asym` for `pcm.!default` so that playback and capture are routed
  independently (dmix/softvol are playback-only; using `type plug` for default
  blocks microphone capture).
- For I2S output + ICS-43434 input, use:
	```
	pcm.speakerbonnet {
		 type hw
		 card sndrpigooglevoi
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
			type hw
			card sndrpigooglevoi
	}

	pcm.softvol {
			type softvol
			slave.pcm "dmixer"
			control.name "PCM"
			control.card sndrpigooglevoi
	}

	ctl.softvol {
			type hw
			card sndrpigooglevoi
	}

	pcm.!default {
			type asym
			playback.pcm "softvol"
			capture.pcm "hw:sndrpigooglevoi"
	}
	```
- This routes playback through the softvol/dmix chain and capture directly to
  the I2S hardware device, both referencing the card by stable name.

## 4. Systemd Service (`/etc/systemd/system/aplay.service`)
- Keeps the audio device open to prevent popping/clicking:
	```
	[Unit]
	Description=Invoke aplay from /dev/zero at system start.

	[Service]
	ExecStart=/usr/bin/aplay -D default -t raw -r 44100 -c 2 -f S16_LE /dev/zero

	[Install]
	WantedBy=multi-user.target
	```
- Enable only if needed.

## 5. Testing Audio
- Use the default device for playback:
	```
	speaker-test -D default -c2 -t wav -r 44100
	```
- Or play a WAV file:
	```
	aplay -D default /usr/share/sounds/alsa/Front_Center.wav
	```
- Ignore warnings about sample rate mismatch if you hear sound; ALSA is resampling.

## 6. Microphone/Input Devices
- `asound.conf` now defines the capture path via `pcm.!default` → `type asym`
  → `capture.pcm "hw:sndrpigooglevoi"`.
- Use `arecord -l` to list capture devices. The ICS-43434 should appear under
  the `sndrpigooglevoi` card.
- Test recording using the default device:
	```
	arecord -D default -f S16_LE -c 2 -r 44100 -d 5 test.wav
	```
  Or directly via the hardware device:
	```
	arecord -D hw:sndrpigooglevoi -f S16_LE -c 2 -r 44100 -d 5 test.wav
	```
- For speech_recognition, use:
	```python
	import speech_recognition as sr
	print(sr.Microphone.list_microphone_names())
	```
	and select the correct device by name or index.

## 7. Common Issues and Solutions
- **No sound:** Use `aplay -l` to list devices and confirm `sndrpigooglevoi` is present. Do not rely on card numbers — they change between boots on CM5/Pi 5.
- **Playback errors with hw:0,0:** Use `default` or `hw:sndrpigooglevoi` for the correct device.
- **HDMI devices present:** `hdmi_ignore_edid_audio=1` stops HDMI being selected as the default sink, but vc4hdmi cards still appear in `aplay -l` and can claim low card numbers. Always reference the I2S card by name.
- **Multiple overlays:** Only enable the one matching your hardware. Comment out `max98357a`, `dual_i2s`, and `i2s-mmap` if `googlevoicehat-soundcard` is active.
- **No input device / microphone not working:** Ensure the ICS-43434 is wired to the Pi's I2S DATA-IN pin. Run `arecord -l` and confirm the `sndrpigooglevoi` card has a capture subdevice. If not, check the overlay is loaded (`dmesg | grep snd`). Note that `i2smic.py` can also install a separate `snd-i2smic-rpi` capture driver, but this is generally not needed when `googlevoicehat-soundcard` is used.
- **`i2smic.py` says "Unsupported Pi board":** CM5 and Pi 5 are now added to the supported model list with `pimodel_select = 2`.

## 8. Summary Table of Key Files

| File/Setting                | Ideal Content/Setting                                                                 |
|-----------------------------|--------------------------------------------------------------------------------------|
| /boot/firmware/config.txt   | Only `dtoverlay=googlevoicehat-soundcard` enabled, `dtparam=audio=on` disabled, `hdmi_ignore_edid_audio=1` |
| /etc/modprobe.d/raspi-blacklist.conf | Empty or all lines commented out                                            |
| /etc/asound.conf            | Use card name `sndrpigooglevoi`; `type asym` default separating playback and capture |
| /etc/systemd/system/aplay.service | As above, optional (prevents pop/click on first audio output)               |
| arecord -l / aplay -l       | Confirm `sndrpigooglevoi` card appears with both playback and capture subdevices     |
| speech_recognition devices  | Use `sr.Microphone.list_microphone_names()` to find the correct input device         |

## 9. General Best Practices
- Reference ALSA cards by **name** (e.g. `sndrpigooglevoi`), not by number -- card numbers can change on every boot on Pi 5 / CM5.
- Only enable one I2S overlay at a time.
- Use `arecord -D default` and `aplay -D default` for basic input/output testing.
- Use speech_recognition's device listing to select the correct mic.



# Terms and Definitions
## Device Tree
A data structure used by the Linux kernel to describe the hardware layout of a system (especially on ARM devices like Raspberry Pi).
The device tree tells the kernel what hardware is present and how to configure it (e.g., enabling I2S audio via overlays like dtoverlay=googlevoicehat-soundcard).
Overlays are small snippets that add or modify device tree entries at boot, enabling specific hardware features.

## Blacklist File
A configuration file (e.g., /etc/modprobe.d/raspi-blacklist.conf) used to prevent certain kernel modules (drivers) from loading automatically.
By "blacklisting" a module, you stop the kernel from loading it at boot, which can be necessary to avoid conflicts or disable unused hardware.
Commenting out lines in this file (adding #) re-enables the module.

[This is an empty file in my pi]

## ALSA (Advanced Linux Sound Architecture)
The main sound system in Linux for handling audio devices, drivers, and sound mixing.
Provides low-level audio device access and configuration via files like /etc/asound.conf.
Applications use ALSA to play, record, and process audio.

## dmix
An ALSA plugin that allows multiple applications to play audio at the same time on hardware that does not support hardware mixing.
Without dmix, only one application could use the sound device at a time.
dmix mixes multiple audio streams in software and sends the result to the hardware.

## softvol
An ALSA plugin that provides software-based volume control.
Useful for hardware that lacks its own volume control (like many I2S amplifiers).
Allows you to adjust the output volume in software, regardless of hardware capabilities.

## i2samp.py
A Python installer script designed to set up I2S audio on a Raspberry Pi.
Automates tasks like enabling device tree overlays, configuring ALSA, and testing audio output.
It modifies system files, installs necessary packages, and ensures the I2S audio device is properly configured.

## /boot/firmware/config.txt

dtparam=audio=on enables the onboard audio (snd_bcm2835). If you are using an external I2S amplifier, you may want to disable this to avoid conflicts

only `dtoverlay=googlevoicehat-soundcard` is needed to enable the I2S audio device for the Google Voice HAT. Other overlays like `i2s-mmap`, `max98357a`, or `dual_i2s` are not necessary and may cause conflicts.



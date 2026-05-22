# I2S Audio — CM5 Carrier Board

## Hardware

| Signal | GPIO | Connected to |
|--------|------|--------------|
| BCLK (I2S clock) | 18 | MAX98357A + ICS-43434 |
| LRCLK (word select) | 19 | MAX98357A + ICS-43434 |
| SDO (TX, data out) | 21 | MAX98357A DIN |
| SDI (RX, data in) | 20 | ICS-43434 DATA (both mics) |
| SD_MODE (amp enable) | 16 | MAX98357A SD |

Two ICS-43434 I2S microphones share the same DATA line (GPIO 20). One has its L/R SELECT pin tied to GND (left channel), the other to 3.3 V (right channel), so they form a stereo pair on a single wire.

The CM5 I2S controller is the Synopsys DesignWare (`snps,designware-i2s`) on the RP1 chip. It supports **`S32_LE` at `48000 Hz` only**.

---

## Device Tree Overlay

The kernel learns about hardware connections through a **Device Tree overlay** — a small binary patch applied at boot that tells the kernel which drivers to load and how to wire them together.

### Files

| File | Purpose |
|------|---------|
| `installers/audio/cm5-i2s-audio.dts` | Human-readable source describing the hardware |
| `cm5-i2s-audio.dtbo` (compiled from above) | Binary patch applied by the bootloader — installed to `/boot/firmware/overlays/` |

The DTS source creates a `simple-audio-card` with **two DAI (Digital Audio Interface) links** on the same I2S controller:

- **DAI link 0** → `invensense,ics43432` codec driver → ALSA PCM **device 0** (capture)
- **DAI link 1** → `maxim,max98357a` codec driver → ALSA PCM **device 1** (playback)

### Why not `googlevoicehat-soundcard`?

The `voicehat-codec` driver only defines a speaker output in its DAPM (Dynamic Audio Power Management) routing. DAPM is how the kernel knows which hardware paths to power up for a given operation. Because the voicehat codec had no capture DAPM route, the RP1's I2S RX engine was never enabled — microphone recordings returned silence regardless of wiring.

The new overlay uses dedicated drivers (`max98357a`, `ics43432`) that have correct DAPM routes for both playback and capture.

### Installing the overlay

`install-audio.sh` (run from the `installers/` directory on the device) compiles the DTS and installs it:

```bash
cd ~/modular-biped/installers
bash install-audio.sh
sudo reboot
```

Requires `dtc` (`sudo apt install device-tree-compiler` if missing).

### `config.txt` entry

```
dtoverlay=cm5-i2s-audio
hdmi_ignore_edid_audio=1
#dtparam=audio=on   ← keep disabled
```

---

## ALSA Configuration (`/etc/asound.conf`)

After reboot the sound card appears as:

```
card 0: cm5i2saudio [cm5-i2s-audio]
  device 0: ics43432-hifi    (capture)
  device 1: MAX98357A HiFi   (playback)
```

The ALSA card number can change between boots when HDMI devices are present, so always reference the card by **name** (`cm5i2saudio`).

`asound.conf` defines a software pipeline on top of the hardware:

- **`pcm.speakerbonnet`** — raw hardware playback (`hw:cm5i2saudio,1`)
- **`pcm.dmixer`** — software mixer so multiple apps can play simultaneously (`type dmix`)
- **`pcm.softvol`** — software volume control on top of dmixer
- **`pcm.mic_plug`** — capture with format conversion (`type plug` over `hw:cm5i2saudio,0`), so apps that request `S16_LE` are transparently converted to the `S32_LE` the hardware requires
- **`pcm.!default`** — `type asym` routes playback and capture independently (dmix/softvol are playback-only; without `asym`, capture would be blocked)

On Raspberry Pi OS Bookworm, PipeWire is the default audio server and overrides `pcm.!default` for most applications. The `asound.conf` chain is used by CLI tools (`aplay`, `arecord`) that access ALSA directly.

---

## Testing

**List devices:**
```bash
aplay -l     # shows device 1 (MAX98357A, playback)
arecord -l   # shows device 0 (ICS-43434, capture)
```

**Speaker test (direct hardware, both channels):**
```bash
speaker-test -D hw:cm5i2saudio,1 -c 2 -r 48000 -t sine -l 1
```

**Microphone test (record 3 s, play back):**
```bash
arecord -D hw:cm5i2saudio,0 -f S32_LE -c 2 -r 48000 -d 3 test.wav
aplay  -D hw:cm5i2saudio,1 test.wav
```

**Via default device (through PipeWire or asound.conf chain):**
```bash
arecord -D default -f S16_LE -c 2 -r 48000 -d 3 /tmp/test.wav
aplay  -D default /tmp/test.wav
```

---

## Speech Recognition (`SpeechInput` module)

The `SpeechInput` module uses the `speech_recognition` library, which requests audio at **16000 Hz**. The hardware only supports 48000 Hz, so a device that handles resampling is required.

The module is configured to use the `pulse` device, which is PipeWire's PulseAudio compatibility interface. This is the correct choice because:

- The direct hardware device (`hw:cm5i2saudio,0`) rejects any sample rate other than 48000 Hz — `speech_recognition`'s 16000 Hz request will fail immediately.
- The `pulse` device routes through PipeWire, which resamples transparently between whatever the application requests and what the hardware needs.

---

## `aplay.service`

This service was originally used to hold the hardware open to prevent a pop on first playback. **Do not enable it on PipeWire systems** — it holds an exclusive ALSA dmix lock and causes PipeWire to time out. `install-audio.sh` explicitly disables it. The service file is kept in the repo only as a reference for pure-ALSA setups.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `aplay -l` shows no `cm5i2saudio` card | Overlay not applied | Check `dmesg \| grep -i "i2s\|max98\|ics43"` for probe errors; confirm `/boot/firmware/overlays/cm5-i2s-audio.dtbo` exists |
| Speaker silent, no errors | SD_MODE GPIO wrong | Verify GPIO 16 is correct for the carrier board; check `pinctrl get 16` |
| Microphone records silence | DAPM not routing capture | Confirm you are using `cm5-i2s-audio` overlay (not `googlevoicehat-soundcard`); check `sudo find /sys/kernel/debug/asoc -name "Capture"` exists |
| `arecord` error: unsupported format | Wrong format for hw device | Use `-f S32_LE` with `hw:cm5i2saudio,0`; use `-f S16_LE` with `default` (plug converts) |
| PipeWire stream timeout | `aplay.service` is running | `sudo systemctl disable --now aplay.service` |

---

## Terms

**Device Tree** — A data structure the bootloader passes to the Linux kernel describing hardware that cannot be auto-detected (I2S buses, GPIO assignments, codec chip connections, etc.).

**DTS (Device Tree Source)** — Human-readable text source file (like `cm5-i2s-audio.dts`).

**DTB (Device Tree Blob)** — The compiled binary form of a DTS, loaded at boot.

**DTBO (Device Tree Blob Overlay)** — A partial DTB patched on top of the base device tree at boot. Pi overlays are `.dtbo` files in `/boot/firmware/overlays/`. `dtoverlay=name` in `config.txt` loads `name.dtbo`.

**DAPM (Dynamic Audio Power Management)** — The ASoC (ALSA System on Chip) subsystem that manages which hardware audio paths are powered at any time. A codec driver must define DAPM widgets and routes for both playback and capture; if a capture route is missing, the I2S RX engine is never enabled even if the hardware supports it.

**DAI (Digital Audio Interface)** — The connection between the CPU-side I2S controller and a codec chip. A sound card can have multiple DAI links (one per codec), each appearing as a separate PCM device in ALSA.

**dmix** — ALSA plugin that software-mixes multiple playback streams so more than one app can play audio simultaneously.

**softvol** — ALSA plugin providing software volume control for hardware that has no built-in mixer.

**asym** — ALSA plugin that routes playback and capture to independent devices, needed when the playback chain (dmix/softvol) cannot handle capture.

**plug** — ALSA plugin that transparently converts sample format and rate between what an application requests and what the hardware supports (e.g. S16_LE → S32_LE).

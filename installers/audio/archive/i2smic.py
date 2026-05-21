import os

try:
    from adafruit_shell import Shell
except ImportError:
    raise RuntimeError("The library 'adafruit_shell' was not found. To install, try typing: sudo pip3 install adafruit-python-shell")

shell = Shell()

def main():
    shell.clear()
    boot_config = shell.get_boot_config()
    print("""This script downloads and installs
I2S microphone support.
""")
    if not shell.is_raspberry_pi():
        shell.bail("Non-Raspberry Pi board detected.")
    pi_model = shell.get_board_model()
    print("{} detected.\n".format(pi_model))
    if pi_model in ("RASPBERRY_PI_ZERO", "RASPBERRY_PI_ZERO_W", "RASPBERRY_PI_B_REV2"):
        pimodel_select = 0
    elif pi_model in ("RASPBERRY_PI_2B", "RASPBERRY_PI_3B", "RASPBERRY_PI_CM3_PLUS", "RASPBERRY_PI_3B_PLUS", "RASPBERRY_PI_3A_PLUS", "RASPBERRY_PI_ZERO_2_W"):
        pimodel_select = 1
    elif pi_model in ("RASPBERRY_PI_4B", "RASPBERRY_PI_CM4", "RASPBERRY_PI_400",
                      "RASPBERRY_PI_5B", "RASPBERRY_PI_CM5", "RASPBERRY_PI_5"):
        pimodel_select = 2
    else:
        shell.bail("Unsupported Pi board detected.")

    auto_load = (
        not shell.argument_exists('noautoload') and
        shell.prompt("Auto load module at boot?", force_arg="autoload"))

    print("""
Installing...""")

    # Get needed packages
    shell.run_command("apt-get -y install git raspberrypi-kernel-headers")

    # Clone the repo
    shell.run_command("git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git")

    # Build and install the module
    shell.chdir("Raspberry-Pi-Installer-Scripts/i2s_mic_module")
    shell.run_command("make clean")
    shell.run_command("make")
    shell.run_command("make install")

    # Setup auto load at boot if selected
    if auto_load:
        shell.write_text_file(
            "/etc/modules-load.d/snd-i2smic-rpi.conf",
            "snd-i2smic-rpi"
        )
        shell.write_text_file(
            "/etc/modprobe.d/snd-i2smic-rpi.conf",
            "options snd-i2smic-rpi rpi_platform_generation={}".format(pimodel_select)
        )

    # Enable I2S overlay
    shell.run_command(f"sed -i -e 's/#dtparam=i2s/dtparam=i2s/g' {boot_config}")

    # Done
    print("""DONE.

Settings take effect on next boot.
""")
    if not shell.argument_exists('noreboot'):
        shell.prompt_reboot(force_arg="reboot")

# Main function
if __name__ == "__main__":
    shell.require_root()
    # Probably not necessary for now because the Pi 5 doesn't work anyway
    if shell.is_raspberry_pi_os() and shell.is_kernel_userspace_mismatched() and shell.is_pi5_or_newer():
        shell.bail("Unable to proceed on Pi 5 or newer boards with a with a 32-bit OS. Please reinstall with a 64-bit OS.")
    shell.check_kernel_userspace_mismatch()
    main()

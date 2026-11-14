# Weather Paper — firmware releases

Flashable firmware only. Source lives offline; this repo exists to hand out builds.

## Download

Grab the files from the [latest release](../../releases/latest).

Two builds, two file types each:

| Build | File | Use |
|---|---|---|
| **Weather Paper** (5.79" panel) | `weather-paper-vX.Y.Z-factory.bin` | First flash over USB — full image including bootloader and partitions |
| | `weather-paper-vX.Y.Z-ota.bin` | Update over the air / web installer — app partition only |
| **Weather Paper Mini** (smaller build) | `weather-paper-min-vX.Y.Z-factory.bin` | First flash over USB |
| | `weather-paper-min-vX.Y.Z-ota.bin` | Update over the air |

## Flashing

**Factory image (USB):** connect the board over USB-C, put it in download mode, then flash
the factory binary at offset `0x0` (`0x1000` for some ESP32 variants) with `esptool.py`,
or drag it into the ESPHome web installer / any ESP32 flasher that accepts a merged image.

**OTA image:** use the device's own update page, or `esphome upload` with the OTA binary.
The OTA file does **not** include the bootloader — a board that has never been flashed
needs the factory image first.

## Checksums

Every release lists MD5 sums in its notes so you can verify a download before flashing.

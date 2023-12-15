import os
import time
from collections import namedtuple

import audiobusio
import audiomp3
import board
import digitalio
import pwmio
import sdcardio
import storage
from microcontroller import Pin

ItemType = namedtuple("ItemType", ("path", "type"))
FOLDER = 0x4000
FILE = 0x8000


class LED:
    """LED object"""

    def __init__(self, pin: Pin = board.SDA) -> None:
        self.led = pwmio.PWMOut(pin, frequency=1000, duty_cycle=0)

    def _convert_brightness(self, value: int) -> int:
        """Converts values between 0 and 255 to values between 0 and 65535"""
        return int(value * (65535 / 255))

    @property
    def brightness(self) -> int:
        """Get the brightness level of the LED"""
        return int(self.led.duty_cycle / (65535 / 255))

    @brightness.setter
    def brightness(self, level: int):
        """Set the brightness level of the LED"""
        level = max(0, min(level, 255))  # Clamp level between 0 and 255
        self.led.duty_cycle = self._convert_brightness(level)

    @property
    def state(self) -> bool:
        """Returns the current state of the LED"""
        if self.led.duty_cycle == 0:
            return False
        return self.led.duty_cycle

    @state.setter
    def state(self, new_state: bool) -> bool:
        """Set the state directly"""
        if new_state:
            self.on()
        else:
            self.off()
        return self.state

    def on(self):
        """Turn on the LED"""
        print("Turning on")
        self.brightness = 255

    def off(self):
        """Turn off the LED"""
        self.brightness = 0

    def toggle(self):
        """Toggle the LED"""
        self.state = not self.state

    def blink(self, num: int, speed: float = 0.25):
        """Blink LED num times"""
        self.off()
        for _ in range(num):
            self.on()
            time.sleep(speed)
            self.off()
            time.sleep(speed)


class SDCard:
    """Reference the SD Card"""

    def __init__(self, mount_point: str = "/sd") -> None:
        self.mount_point = mount_point
        print("Creating card")
        card = sdcardio.SDCard(board.SPI(), board.A0)
        print("Loading Filesystem")
        vfs = storage.VfsFat(card)
        print("Mouning SD Card")
        storage.mount(vfs, self.mount_point)
        print("SD Card Mounted")

    def ls(self, folder: str = "/") -> list[tuple[str, str]]:
        """
        List files and folder on the SD Card

        Returns a list with all items in the folder with a tuple of path and the type
        """
        path = self.mount_point + folder
        items = []
        for i in os.listdir(self.mount_point + folder):
            f = f"{path}/{i}"
            t = os.stat(f)[0]
            items.append(ItemType(f, FILE if t == FILE else FOLDER))
        return items

    def ls_files(self, folder: str = "/", ext: str = "") -> list:
        """Returns a list of files in a folder optionally filtered by extension"""
        return [f for f in self.ls(folder) if f.type == FILE & f.path.endswith(ext)]


class AudioOut:
    """Audio Player"""

    def __init__(self) -> None:
        self.audio = audiobusio.I2SOut(board.A3, board.A2, board.A1)

    def play(self, file: str, led: LED | None = None):
        """Play a WAV file"""
        with open(file, "rb") as f:
            wave = audiomp3.MP3Decoder(f)
            self.audio.play(wave)
            print(f"Playing {file}")
            if led:
                led.off()
            while self.audio.playing:
                if led:
                    level = wave.rms_level * 3
                    led.brightness = level
                time.sleep(0.1)
            led.off()
            print("finished")


class Button:
    """Button object"""

    def __init__(self, button: Pin = board.BUTTON, debounce: float = 0.2) -> None:
        self.button = digitalio.DigitalInOut(button)
        self.button.switch_to_input(pull=digitalio.Pull.UP)
        self.debounce = debounce

    @property
    def pressed(self) -> bool:
        """Return the value of the button with debounce"""
        if not self.button.value:
            time.sleep(self.debounce)
            return True
        return False


def normalize_scale(value: int, in_min: int, in_max: int, out_min: int, out_max: int):
    """Normalize a value from one scale to another"""
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

"""Play music on Mr Bear"""
import os
import time

import audiobusio
import audiomp3
import board
import digitalio
import neopixel
import sdcardio
import storage
from microcontroller import Pin

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)


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

    def ls(self, ext: str = "wav") -> list[str]:
        """List files on the SD Card"""
        return [
            file for file in os.listdir(self.mount_point) if file.endswith(ext)
        ]  # noqa: E501


class AudioOut:
    """Audio Player"""

    def __init__(self) -> None:
        self.audio = audiobusio.I2SOut(board.A3, board.A2, board.A1)

    def play(self, file: str):
        """Play a WAV file"""
        with open(file, "rb") as f:
            wave = audiomp3.MP3Decoder(file)
            self.audio.play(wave)
            print(f"Playing {file=}")
            while self.audio.playing:
                pass
            print("finished")


class Button:
    """Button object"""

    def __init__(self, button: Pin = board.BUTTON) -> None:
        self.button = digitalio.DigitalInOut(button)
        self.button.switch_to_input(pull=digitalio.Pull.UP)

    @property
    def pressed(self) -> bool:
        """Return the value of the button with debounce"""
        if not self.button.value:
            time.sleep(0.2)
            return True
        else:
            return False


class LED:
    """LED object"""

    def __init__(self) -> None:
        self.led = neopixel.NeoPixel(board.NEOPIXEL, 1)
        self._state = False

    @property
    def state(self) -> bool:
        """Returns the current state of the LED"""
        return self._state

    @state.setter
    def state(self, new_state: bool) -> bool:
        """Set the state directly"""
        if new_state:
            self.on()
        else:
            self.off()
        return self._state

    def on(self):
        """Turn on the LED"""
        self._state = True
        self.led.fill(GREEN)

    def off(self):
        """Turn off the LED"""
        self._state = False
        self.led.fill(BLACK)


if __name__ == "__main__":
    sdcard = SDCard()
    audio = AudioOut()
    button = Button()
    led = LED()

"""Play music on Mr Bear"""
import os
import time
from collections import namedtuple

import audiobusio
import audiomp3
import board
import digitalio
import neopixel
import sdcardio
import storage
from microcontroller import Pin

ItemType = namedtuple("ItemType", ("path", "type"))
FOLDER = 0x4000
FILE = 0x8000


class LED:
    """LED object"""

    def __init__(self) -> None:
        self.led = neopixel.NeoPixel(board.NEOPIXEL, 1)
        self._state = False
        self.color = (255, 0, 0)  # GREEN

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
        self.led.fill((255, 0, 0))

    def off(self):
        """Turn off the LED"""
        self._state = False
        self.led.fill((0, 0, 0))

    def blink(self, num: int, speed: float = 0.25):
        """Blink LED num times"""
        for _ in range(num):
            self.on()
            time.sleep(speed)
            self.off()
            time.sleep(speed)

    @property
    def brightness(self) -> float:
        return self.led.brightness

    @brightness.setter
    def brightness(self, level: float):
        level = level / 100
        print("Pre clamp level: ", level)
        self.led.brightness = 1 if level > 1 else level
        print("Post clamp level: ", self.led.brightness)


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
                led.brightness = 0
                led.on()
            while self.audio.playing:
                if led:
                    level = wave.rms_level
                    print("RMS Level: ", level)
                    led.brightness = level
                time.sleep(0.1)
            led.off()
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
        return False


if __name__ == "__main__":
    sdcard = SDCard()
    audio = AudioOut()
    button = Button()
    led = LED()

    print("Loaded and ready")
    led.blink(3)

    # Stop annoying regular blink LED
    import supervisor

    supervisor.runtime.rgb_status_brightness = 0

    while True:
        if button.pressed:
            song = sdcard.ls("/")[0].path
            audio.play(song, led)

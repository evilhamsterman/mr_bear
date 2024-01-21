import random
import time
from pathlib import Path

import adafruit_logging as logging
import alarm
import board
import digitalio
import sdcardio
import supervisor
from audiobusio import I2SOut
from audiomp3 import MP3Decoder
from microcontroller import Pin
from pwmio import PWMOut
from storage import VfsFat, mount

log = logging.getLogger("mr_bear")


class LED:
    """LED object"""

    def __init__(self, pin: Pin = board.SDA) -> None:
        self.led = PWMOut(pin, frequency=1000, duty_cycle=0)

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

    def __init__(self, mount_point: str | Path = Path("/sd")) -> None:
        self.mount_point = mount_point
        card = sdcardio.SDCard(board.SPI(), board.A0)
        vfs = VfsFat(card)
        mount(vfs, str(self.mount_point))

    def ls(self, folder: str | Path = None) -> list[Path]:
        """Returns a list of items in a folder"""
        if folder is None:
            folder = Path(self.mount_point)
        else:
            folder = Path(self.mount_point) / folder
        return list(folder.iterdir())

    def ls_files(self, folder: str | Path = None, ext: str = None) -> list[Path]:
        """Returns a list of files in a folder optionally filtered by extension"""
        if folder is None:
            folder = Path(self.mount_point)
        if ext is None:
            return [f for f in self.ls(folder) if f.is_file()]
        else:
            return [f for f in self.ls(folder) if f.is_file() and f.suffix == ext]


class Audio:
    """Audio Player"""

    def __init__(self) -> None:
        self.audio = I2SOut(board.A3, board.A2, board.A1)
        self._decoder = None

    def play(self, file: str | Path):
        """Play an MP# file"""
        # Because everything else is unaware of Path objects
        file = str(file)
        if self._decoder is None:
            self._decoder = MP3Decoder(file)
        else:
            self._decoder.open(file)
        log.info(f"Playing {file}")
        self.audio.play(self._decoder)

    def stop(self):
        """Stop playing"""
        log.info("Stopping")
        self.audio.stop()

    @property
    def playing(self) -> bool:
        """Returns the current state of the audio"""
        return self.audio.playing

    def pulse_led(self, led: LED):
        """Pulse the LED to the music"""
        level = self._decoder.rms_level * 2
        log.debug(f"RMS Level: {level}")
        led.brightness = level


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


class App:
    """Main application class"""

    def __init__(self):
        self.sdcard = SDCard()
        self.audio = Audio()
        self.led = LED()

        if supervisor.runtime.serial_connected:
            log.setLevel(logging.INFO)
            log.addHandler(logging.StreamHandler())
        else:
            log.setLevel(logging.ERROR)
            log.addHandler(logging.FileHandler("/sd/mr_bear.log"))

        # Stop annoying regular blink LED
        supervisor.runtime.rgb_status_brightness = 0

        log.info("Loaded and ready")

    def run(self):
        """Run the main loop"""
        left_button = Button(board.RX)
        right_button = Button(board.TX)
        if alarm.wake_alarm:
            file = random.choice(self.sdcard.ls_files("", ".mp3"))
            self.audio.play(file)

        while self.audio.playing:
            log.info("Entering loop")
            if left_button.pressed or right_button.pressed:
                self.audio.stop()
            if self.audio.playing:
                self.audio.pulse_led(self.led)
            time.sleep(0.1)
        else:
            log.info("Audio done")
            self.led.off()
            left_button.button.deinit()
            right_button.button.deinit()
            left_alarm = alarm.pin.PinAlarm(pin=board.RX, value=False, pull=True)
            right_alarm = alarm.pin.PinAlarm(pin=board.TX, value=False, pull=True)
            log.info("Entering deep sleep")
            alarm.exit_and_deep_sleep_until_alarms(left_alarm, right_alarm)

"""Play music on Mr Bear"""
import random
import time
from pathlib import Path

import board

from objects import LED, AudioOut, Button, SDCard

if __name__ == "__main__":
    sdcard = SDCard()
    audio = AudioOut()
    left_button = Button(board.TX)
    right_button = Button(board.RX)
    led = LED()
    left_dir = Path("left")
    right_dir = Path("right")

    # Stop annoying regular blink LED
    import supervisor

    supervisor.runtime.rgb_status_brightness = 0

    print("Loaded and ready")
    led.blink(3)

    while True:
        if left_button.pressed:
            file = random.choice(sdcard.ls_files(left_dir, ".mp3"))
            audio.play(file, led)
            time.sleep(0.1)
        if right_button.pressed:
            file = random.choice(sdcard.ls_files(right_dir, ".mp3"))
            audio.play(file, led)
            time.sleep(0.1)

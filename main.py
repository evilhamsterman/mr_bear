"""Play music on Mr Bear"""
import board

from objects import LED, AudioOut, Button, SDCard

if __name__ == "__main__":
    sdcard = SDCard()
    audio = AudioOut()
    left_button = Button(board.TX)
    right_button = Button(board.RX)
    led = LED()

    print("Loaded and ready")
    led.blink(3)

    # Stop annoying regular blink LED
    import supervisor

    supervisor.runtime.rgb_status_brightness = 0

    while True:
        if left_button.pressed:
            audio.play("/sd/left/left_button.mp3", led)
        if right_button.pressed:
            audio.play("/sd/right/right_button.mp3", led)

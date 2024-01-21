"""Play music on Mr Bear"""

from supervisor import reload

from mr_bear import App, log

app = App()

if __name__ == "__main__":
    log.info("Starting Mr Bear")
    try:
        app.run()
    except Exception as e:
        log.error(e)
        app.led.blink(5)
        reload()

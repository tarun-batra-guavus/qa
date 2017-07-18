from potluck.ui import ui
from potluck.logging import logger
from lib.ui import appreflex

try:
    ui.launchBrowser()

    logger.info("Waiting for UI to open")
    waitVanish("appreflex_loading_message.png")

    appreflex.login("admin", "Admin@656")

    # Wait for logged-in username to be visible
    wait("appreflex_logged_in_user.png", 15)
    ui.passed()
except:
    ui.failed()
finally:
    ui.cleanup()

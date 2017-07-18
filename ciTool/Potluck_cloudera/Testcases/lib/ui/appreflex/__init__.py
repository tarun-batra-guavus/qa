from potluck import sikuli
from potluck.logging import logger

import os

CUSTOM_IMAGES_PATH = os.path.abspath(os.path.dirname(__file__))
def setup_paths():
    if CUSTOM_IMAGES_PATH not in list(sikuli.getImagePath()):
        sikuli.addImagePath(CUSTOM_IMAGES_PATH)

def login(username="admin", password="admin123"):
    setup_paths()
    logger.debug("In appreflex.login")
    sikuli.wait("login_box.png", 30)

    # Sometimes, login box readjusts its position
    sikuli.wait(5)
    login_box = sikuli.find("login_box.png")
    login_box.highlight(2)

    # Get the location of username and password boxes
    username_box_location = login_box.getTopLeft().offset(40, 40)
    password_box_location = login_box.getTopLeft().offset(40, 80)

    login_box.click()   # To get the focus (if not already have it)

    sikuli.type(username_box_location, username)
    sikuli.type(password_box_location, password)

    sikuli.click("signin_button.png")

def export_to_csv(output_file):
    logger.debug("In appreflex.export_to_csv")
    logger.info("Saving output csv at: %s" % output_file)
        
    click("1397810346809.png")
    wait("1402486200633.png")

    click("1402486225820.png")
    wait("1402486243696.png")

    click ("1402486256352.png")
    wait ("1402486274462.png")

    click ("1402486306743.png") 
    wait ("1402486363806.png")

    paste(output_file)
    
    click ("1402486392510.png")

    if exists("1403156988313.png"):
        click ("1403157013219.png")
        
if __name__ == "__main__":
    #Testing purposes
    login()
    export_to_csv()

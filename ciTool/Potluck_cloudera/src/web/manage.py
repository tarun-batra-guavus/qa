#!/usr/bin/env python
import os
import sys

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
MODULES_DIR = os.path.join(ROOT_DIR, "modules")
MODULES_ZIP = os.path.join(ROOT_DIR, "modules.zip")

sys.path.insert(0, MODULES_ZIP)
sys.path.insert(0, MODULES_DIR)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

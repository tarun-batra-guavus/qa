from django.conf import settings
from django.utils.safestring import mark_safe

import os
import logging
import re
import itertools

logger = logging.getLogger(__name__)

def find_all_files(directory, patterns=[]):
    """
    Find all files in a directory(recursively), and filter them with patterns

    :argument patterns: List of glob patterns. If a pattern starts with `!`, its
                        effect is negated. Make sure to include the negative patterns in the end
    """
    files = []
    for root, dirnames, filenames in os.walk(directory):
        if root[0] == ".":
            # Skip hidden folders
            continue

        for filename in filenames:
            if filename[0] == ".":
                # Skip hidden files
                continue
            rel_path = os.path.relpath(os.path.join(root, filename), directory)
            files.append(rel_path)

    # Filter the files, if a pattern is defined
    if patterns:
        filtered_filenames = []
        for pattern in patterns:
            if pattern.startswith("!"):
                pattern = re.compile(pattern[1:])
                # Keep only those files which does not match this pattern
                files = itertools.ifilterfalse(pattern.search, files)
            else:
                pattern = re.compile(pattern)
                files = itertools.ifilter(pattern.search, files)

    return files

def check_testbed_owner(testbed_path, user):
    if testbed_path.startswith("/"):
        actual_testbed_path = testbed_path
    else:
        actual_testbed_path = os.path.join(settings.POTLUCK.USER_TESTBEDS_DIR, testbed_path)
    actual_testbed_dir = os.path.dirname(actual_testbed_path)
    expected_testbed_dir = os.path.join(settings.POTLUCK.USER_TESTBEDS_DIR, user.username)
    logger.info("Actual testbed dir: %s, Expected Dir: %s" % (actual_testbed_dir, expected_testbed_dir))
    return actual_testbed_dir == expected_testbed_dir

def process_logs_for_html(fh):
    #return fh.read()
    return mark_safe(re.sub("[^\n]*\[(DEBUG|INFO|ERROR|FAILED|NOTICE|WARNING)\][^\n]*", r"<span class='\1'>\g<0></span>", fh.read()))

#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Code imported into all processes before starting.
    Setup for different process types is delegated here
"""

import os
import uwsgi


print("# SHARED import: %s" % os.getpid())


if uwsgi.masterpid() == os.getpid():
    from .master import master_startup
    master_startup()

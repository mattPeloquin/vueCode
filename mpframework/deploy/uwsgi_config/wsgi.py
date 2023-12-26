#!/usr/bin/env python
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    uWSGI Django wsgi application
    Run by uWSGI workers to service every request.
"""
import os

from ...common.deploy.wsgi_app import get_mpwsgi_application


print("# --- Creating WSGI app: %s ---" % os.getpid())

wsgi_app = get_mpwsgi_application()

print("# --- WSGI app created: %s ---" % os.getpid())

#!/usr/bin/env python
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django manage.py for MPF

    Manage starts a new process to run django commands
    or dev servers with environment variables and
    MPF settings from configuration profiles.
"""
import sys
from django.db import DatabaseError
from django.core.management import execute_from_command_line

from mpframework.common.deploy.settings import setup_env_config


command = ' '.join( sys.argv[1:] )
print("\n====>>>  %s  <<<====\n" % command)

try:
    # Setup MPF settings
    setup_env_config( argv=sys.argv )

    try:
        # Hand off to Django to run its local dev webserver or a command
        execute_from_command_line( sys.argv )

    except DatabaseError as e:
        if 'no such table' in str(e):
            print("\n\n >>>  Is a DB setup for this platform/profile?  <<<\n")
        raise
except Exception as e:
    print("Framework management exception: %s -> %s" % (command, e))
    raise

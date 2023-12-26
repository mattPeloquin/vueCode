#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mySQL utility functions
"""

from django.db import connections


def open_connections():
    """
    Return currently open connections for this thread
    """
    rv = []
    for db_name in connections:
        try:
            rv.append( getattr( connections._connections, db_name ) )
        except AttributeError:
            continue
    return rv

#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mySQL utility functions
"""

from django.db import connections
from django.db.utils import OperationalError

from .. import log


def db_connection_retry( fn ):
    """
    Decorator for handling retries when a DB connection gets closed or is
    briefly unavailable. Try resetting the connections for this thread
    and calling the function again.
    NOTE - OperationalError must be raised up the stack for this to work
    """
    def wrap( *args, **kwargs ):
        try:
            return fn( *args, **kwargs )
        except OperationalError as e:
            log.info("Retrying DB OperationalError: %s -> %s", fn, e)
            connections.close_all()
        return fn( *args, **kwargs )
    return wrap


def create_mysql_db( db_info ):
    """
    Create a new DB on mySQL host

    Django sync behavior won't create a new DB in a mySQL database,
    so to make sync behave the same for mySQL/RDS as for sqllite,
    use this method in sync and test to create DB
    """
    log.info("Ensuring DB is created: %s", db_info)

    db_host = db_info.get('HOST')
    log.info("Connecting to DB Server: %s", db_host)
    import MySQLdb
    db = MySQLdb.connect( host=db_host,
                          user=db_info.get('USER'),
                          passwd=db_info.get('PASSWORD') )

    db_name = db_info.get('NAME')
    cursor = db.cursor()
    try:
        cursor.execute("create database %s;" % db_name)
        log.info("DB created: %s", db_name)
    except Exception as e:
        # No worries, this will be the nominal case for clusters
        log.info("DB NOT created: %s", e)

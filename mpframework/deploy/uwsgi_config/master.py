#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Code run only in the master early after startup, before forking

    NOTE - experiments placing worker threads (such as SQS polling)
    in the master process lead to deadlock where threads and/or
    the entire server are not responsive.
"""
import os
import uwsgi


def master_startup():

    print("# MASTER STARTUP: %s" % os.getpid())

    # Setup MPF environment in master before forking
    from mpframework.common.deploy.settings import setup_env_config
    setup_env_config( wsgi=True )

    # Register signals in master to be forked into workers
    from mpframework.common.deploy.server import uwsgi_register
    uwsgi_register()

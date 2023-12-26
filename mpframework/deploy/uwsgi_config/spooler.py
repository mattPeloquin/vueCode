#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Code run in spooler process before starting
"""
import os
import uwsgi

from mpframework.common.tasks import spool_handler


print("# SPOOLER import: %s" % os.getpid())

# Spool handler is documented to be set in the master process,
# but only works if set here when spooler is loaded
# (spool_handler seems to get reset during startup)
uwsgi.spooler = spool_handler

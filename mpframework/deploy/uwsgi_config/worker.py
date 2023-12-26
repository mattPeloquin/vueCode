#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Code run in worker/spooler process before starting.
    Typically loaded once in master process and forked, but may
    vary depending on how uwsgi process loading is setup.
"""
import os
import uwsgi


print("# WORKER import: %s (%s)" % (uwsgi.worker_id(), os.getpid()))


# For lazy apps, let the ops app send startup signal when loaded
# Otherwise, delay startup until after uWSGI master forking
if not uwsgi.opt.get('lazy-apps'):
    print("# Postfork mode: %s" % os.getpid())
    from uwsgidecorators import postfork

    @postfork
    def _postfork_processing():
        print("# POSTFORK: %s(%s)" % (uwsgi.worker_id(), os.getpid()))

        if uwsgi.masterpid() != os.getpid():
            from mpframework.foundation.ops.signals import startup_signal
            startup_signal.send( sender=__name__ )

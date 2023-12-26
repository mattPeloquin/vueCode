#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    One-off temp cleanup placeholder

    Use to run custom code for DB updates from ops console, usually
    within a repsone/request cycle on prod-mpd server,
"""


def one_off_cleanup( log, sandbox, commit, limit, constraint ):
    log.info("CLEANUP => %s, commit(%s), limit(%s), constraint(%s)",
                sandbox, commit, limit, constraint)

    limit_count = 0
    limit = int(limit) if limit else 5
    start = int(constraint) if constraint else None
    stop = start + limit if start and limit else limit

    from mpextend.product.account.models import APA

    qs = APA.objects.filter().order_by('id')[ start:stop ]

    for obj in qs.iterator():
        msg = str(obj)

        """
        if obj._history:

            if not obj.data['history']:
                obj.data.set( 'history', obj._history )
                obj.save( modify_time=False )
                msg += "TRANSFERRED: " + str(obj._history)[:30]
                limit_count += 1
            else:
                msg += "DATA ALREADY: " + obj.data['history'][:30]
        """

        log.info( "%s", msg )
        if limit and limit_count > limit:
            log.info("Stopping due to limit of %s: ", limit)
            break

    log.info("CLEANUP COMPLETE")

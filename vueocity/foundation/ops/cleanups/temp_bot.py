#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    One-off temp bot placeholder
"""
from django.core.cache import caches

from mpframework.common import log
from mpframework.common.tasks import mp_async
from mpframework.common.tasks.bots import bot_start
from mpframework.common.tasks.bots import bot_state
from mpframework.common.tasks.bots import bot_next
from mpframework.common.tasks.bots import bot_stop


def stop_temp_bot():
    bot_stop('TEMP_BOT')

def start_temp_bot( log, sandbox, commit, limit, constraint ):
    log.info("TEMP BOT => %s, commit(%s), limit(%s), constraint(%s)",
                sandbox, commit, limit, constraint)

    limit = int(limit) if limit else 2
    start = int(constraint) if constraint else None
    stop = start + limit if start and limit else limit

    state = {
        'init': {
            'limit': limit,
            'start': start,
            'stop': stop,
            },
        'current': {
            'count': 0,
            },
        }

    bot_start( 'TEMP_BOT', _temp_bot_fn, state )


from django.db import models
from django.conf import settings

from mpframework.common.model.fields import mpDateTimeField
from mpframework.common.utils import dt

from mpframework.common.aws import get_client



def full_domain_name( name ):
    return "{}-{}".format( settings.MP_PLAYPEN, name )

def sdb_domain( name ):
    return get_client('sdb'), full_domain_name( name )



def events( request ):

    events = []

    if 'POST' == request.method:
        query = request.POST.get('query')

        if 'raw' in request.POST:
            where = query
        else:
            if 'user' in request.POST:
                where = "where `user_id` = '{}'".format( query )

            elif 'sandbox' in request.POST:
                where = "where `sandbox_id` = '{}'".format( query )

            elif 'event' in request.POST:
                where = "where `event` like '%{}%'".format( query )

            elif 'time' in request.POST:
                where = "where `time` like '%{}%'".format( query )

            sort = request.POST.get('sort')
            limit = request.POST.get('limit')
            if sort:
                where += " order by `{}`".format( sort )
            if limit:
                where += " limit {}".format( limit )

        client, domain = sdb_domain('StudentEvent')
        query ="select * from `%s` %s" % ( domain.name, where )

        log.info2("SDB QUERY: %s", query)
        events = domain.select( query )

    return events


@mp_async
def _temp_bot_fn( **kwargs ):
    state = bot_state( 'TEMP_BOT', **kwargs )
    if not state:
        return
    init = state['init']
    current = state['current']
    current['count'] += 1

    for old in OLDUserTracking.objects.exclude( logins=0 )[:10]:
        log.info( "UPDATING %s:%s, %s %s %s", old.id, old.user_id, old.logins,
                    old.ip_address, old.last_update )

        ut = UserTracking.objects.get_quiet( user_id=old.user_id )
        if ut:
            log.info( "Updating: %s %s", ut.id, ut.user.email )

            ut.logins += old.logins
            ut.seconds += old.seconds
            log.info("logins: %s, seconds: %s", ut.logins, ut.seconds )
            if not ut.ip_address:
                ut.ip_address = old.ip_address
                log.info("IP: %s", ut.ip_address)

            if ut.last_update.date() == dt('2020-12-14').date():
                ut.last_update = old.last_update
                log.info("LastUpdate: %s", ut.last_update)

            ut.save()

        else:
            log.info( ">>> COULD NOT FIND: %s %s", old.id, old.user_id )

        old.logins = 0
        old.save()

    if init['limit'] > current['count']:
        state['current'] = current
        bot_next( 'TEMP_BOT', _temp_bot_fn, state, **kwargs )


class OLDUserTracking( models.Model ):

    user_id = models.IntegerField()

    last_update = mpDateTimeField()

    ip_address = models.CharField( blank=True )
    seconds = models.IntegerField( default=0 )

    # Values for DB sorting or searching
    logins = models.IntegerField( default=0 )

    objects = models.Manager()

    class Meta:
        db_table = 'user_OLDusertracking'


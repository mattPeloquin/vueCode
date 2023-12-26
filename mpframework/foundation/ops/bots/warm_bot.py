#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Warm the cache for active sandboxes
"""
import requests
from django.conf import settings
from django.urls import reverse

from mpframework.common import log
from mpframework.common.utils import timedelta_past
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import Bot
from mpframework.foundation.tenant.models import Sandbox
from mpframework.user.mpuser.models import mpUser

# Skip the root sandbox
STARTING_SANDBOX = 2

# Number of months used to determine active site
WEEKS_SINCE_USE = settings.MP_ROOT['ACTIVE_SITE_WEEKS']

@mp_async
def warm_bot_fn( **kwargs ):
    state = WarmBot.state( **kwargs )
    if state:
        sandbox = _get_next_sandbox( state )
        if sandbox:
            _warm_site( sandbox )
        WarmBot.next( state, **kwargs )

class WarmBot( Bot ):
    NAME = 'BOT_WARM'
    FN = warm_bot_fn
    INITIAL_STATE = {
        'next_sandbox': STARTING_SANDBOX,
        }
WarmBot.register()


def _get_next_sandbox( state ):
    """
    Get the next sandbox that falls within active range, or
    rollover to the first.
    """
    sandbox = Sandbox.objects.mpusing('read_replica')\
                .filter( pk__gte=state['next_sandbox'] )\
                .first()
    if not sandbox:
        log.debug("BOT - WarmBot resetting: %s", sandbox)
        state['next_sandbox'] = STARTING_SANDBOX
        return _get_next_sandbox( state )

    state['next_sandbox'] = sandbox.pk + 1

    # Check if any users for the site have been active
    rv = None
    active_date = timedelta_past( weeks=WEEKS_SINCE_USE )
    active_user = mpUser.objects.mpusing('read_replica')\
                .filter( _sandbox_id=sandbox.pk, last_login__gt=active_date )\
                .first()
    if active_user:
        rv = sandbox
    else:
        log.debug("BOT - WarmBot ignoring inactive: %s", sandbox)

    return rv

def _warm_site( sandbox ):
    """
    The best way to warm content and template caching for a given
    site is to make a request to it vs. making direct calls to
    intermediate cache levels.
    """
    log.info2("BOT - WarmBot warming site: %s", sandbox)
    requests.get( sandbox.portal_url() )
    requests.get( sandbox.host_url( reverse('bootstrap_content') ) )

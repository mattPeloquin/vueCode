#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Asynchronous update of user tracking.

    This module needs to be loadable by the spooler, so some
    imports are in functions to allow import from parent.
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common import sys_options
from mpframework.common import constants as mc
from mpframework.common.logging.timing import mpTiming
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import run_queue_function
from mpframework.common.utils import dt
from mpframework.common.utils import now
from mpextend.common.request_info import get_ip_info
from mpextend.common.request_info import safe_user_agent
from mpextend.common.request_info import get_device_info


def update_for_request( request, new_login=False ):
    """
    Tracking updates performed for each request based on request data.
    """
    if sys_options.disable_non_critical():
        return
    path = request.path
    if request.is_lite or request.is_api or request.is_bad:
        log.debug2("Tracking skip request: %s -> %s", request.mpipname, path)
        return
    sandbox = request.sandbox
    if not sandbox:
        log.debug2("Tracking skip no-host: %s -> %s", request.mpipname, path)
        return
    if sandbox.options['tracking.no_user']:
        log.debug2("Tracking skip option: %s -> %s", request.mpipname, path)
        return

    user = request.user
    if user.is_authenticated:
        log.debug("Tracking user: %s -> %s", user, path)
    else:
        if( not sandbox.flag('TRACKING_visitors') or
                sandbox.options['tracking.no_visitor'] ):
            log.debug2("Tracking skip visitor: %s -> %s", user, path)
            return
        log.debug("Tracking visitor: %s -> %s", user, path)

    values = {
        'user_id': user.pk,
        'sandbox_id': sandbox.pk,
        'provider_id': sandbox._provider_id,
        'ip': request.ip,
        'new_login': new_login,
        'session': request.session and request.session.session_key,
        'user_agent': safe_user_agent( request ),
        'time_now': now(),
        # These values are used for timeseries
        'url': request.uri[ :mc.CHAR_LEN_PATH ],
        'referrer': request.referrer,
        }
    run_queue_function( _update_for_request, sandbox, values=values )

@mp_async
def _update_for_request( **kwargs ):
    """
    Task to update user tracking for requests.
    This works polymorphically on mpUsers and Visitors; only a subset
    of tracking is implemented for Visitors.
    """
    from mpframework.foundation.tenant.models import Sandbox
    from mpframework.user.mpuser.models import mpUser
    from .models import VisitorTracking
    t = mpTiming()
    log.timing("%s Starting user request tracking: %s", t, kwargs)
    values = kwargs.pop('values')
    is_user = bool( values['user_id'] )
    new_login = values['new_login']
    session = values['session']
    time_now = values['time_now']

    if is_user:
        user = mpUser.objects.get( id=values['user_id'] )
        tracking = user.tracking
        tracking.ip_address = values['ip']
    else:
        tracking, _ = VisitorTracking.objects.get_or_create(
                    sandbox_id=values['sandbox_id'], ip_address=values['ip'] )

    # User-specific updates
    if is_user:
        if new_login:
            # Setup a new session
            tracking.logins += 1
        else:
            # Add time increment from last request
            tracking.set_time( time_now )
    # Visitor specific updates
    else:
        tracking.requests += 1

    if session:
        tracking.sessions[ session ] = {
            'active': True,
            'last_time': dt(time_now),
            'last_ip': tracking.ip_address,
            }

    # Data captured in all cases
    tracking.ips[ tracking.ip_address ] = get_ip_info( tracking.ip_address )
    tracking.devices[ tracking.ip_address ] = get_device_info(
                values['user_agent'] )
    tracking.last_update = time_now

    tracking.save()

    # Check for session reduction on user new logins
    if new_login:
        sandbox = Sandbox.objects.get_sandbox_from_id(
                    values['sandbox_id'], values['provider_id'] )
        maximum = sandbox.options['access.max_sessions']
        tracking.reduce_extra_sessions( session, maximum )

    if not settings.MP_TEST_NO_LOG:
        log.info("<- %s User request tracking: %s", t, tracking)

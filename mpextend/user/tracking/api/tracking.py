#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User tracking API
"""

from mpframework.common import log
from mpframework.common.utils import now
from mpframework.common.utils import timedelta_minutes
from mpframework.common.api import respond_api_call
from mpframework.common.view import staff_required

from ..models import UserTracking


@staff_required
def get_active_users( request ):
    """
    Retrieves a list of active user tracking which is returned
    as plain JSON for easier manipulation with JavaScript.

    NOTE - Don't put the session key or IP address here for security reasons
    """
    sandbox = request.sandbox
    minutes = request.GET.get('minutes')
    max_users = request.GET.get('max_users')
    _now = now()
    log.debug("Sandbox user tracking records: %s -> %s, %s", sandbox, minutes, max_users)

    # Get the latest set of users
    user_trackings = []
    for ut in UserTracking.objects.recent_sandbox( sandbox, minutes, max_users ).iterator():
        user = ut.user

        # Skip root user sandbox spoof tracking
        if user.is_root:
            continue

        minutes_since_update = timedelta_minutes( _now - ut.last_update )

        user_data = {
            'id': user.pk,
            'email': user.email,
            'name': user.name,
            'minutes': ut.minutes,
            'logins': ut.logins,
            'last_update': minutes_since_update,
            'days_ago': 1 + minutes_since_update // 60 // 24,
            'geoip': ut.geoip.dict,
            'device': ut.device,
            'sessions_active': len( ut.active_sessions ),
             }

        user_trackings.append( user_data )

    def handler( _payload ):
        tracking_info = { 'user_trackings': user_trackings }
        log.debug_values("Sending active user info: %s", tracking_info)
        return tracking_info

    return respond_api_call( request, handler, methods=['GET'] )

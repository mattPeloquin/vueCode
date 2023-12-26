#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User tracking manager
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.utils import safe_int
from mpframework.common.utils import timedelta_past
from mpframework.common.model import BaseManager


class UserTrackingManager( BaseManager ):

    def create_obj( self, **kwargs ):
        user = kwargs['user']
        if not user.is_root:
            log.info3("Creating new user tracking record: %s", user)
            return super().create_obj( user=user )

    def _recent( self, qf, minutes, max_users ):
        """
        Implementation for recent records.
        Retrieves the latest set users within the timeout
        period and max tracking window.
        """
        minutes = minutes if minutes else settings.MP_TRACKING['WINDOW']
        cutoff = timedelta_past( minutes=minutes )
        max_recent = settings.MP_TRACKING['MAX_RECENT']
        max_users = safe_int( max_users )
        max_records = min( max_users, max_recent ) if max_users else max_recent
        log.info2("Getting active users for: %s -> %s -> %s", qf, cutoff, max_records)
        qf.update({ 'last_update__gte': cutoff })
        return self.mpusing('read_replica')\
                   .select_related('user')\
                   .filter( **qf )\
                   .order_by('-last_update')\
                   [ :max_records ]

    def recent_sandbox( self, sandbox, minutes=None, max=None ):
        return self._recent( {'user___sandbox': sandbox }, minutes, max )

    def recent_provider( self, provider, minutes=None, max=None ):
        return self._recent( {'user___provider': provider }, minutes, max )

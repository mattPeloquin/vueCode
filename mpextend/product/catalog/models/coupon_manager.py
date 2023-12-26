#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Coupon model
"""
from django.db.models import Q

from mpframework.common import log
from mpframework.common.utils import now
from mpframework.common.utils.strings import intersection_comma_lists
from mpframework.foundation.tenant.models.base import TenantManager


class CouponManager( TenantManager ):

    def coupon_search( self, sandbox, code, **kwargs ):
        """
        Get coupon referred to by code or id.
        """
        if not code:
            return
        q = self.model.search_Q( **kwargs )
        query = Q( code__iexact=code )
        try:
            query |= Q( id=int(code) )
        except Exception:
            pass
        q.append( query )
        rv = self.mpusing('read_replica')\
                .filter( *q, sandbox=sandbox )\
                .first()
        log.debug("Coupon search: %s, %s, %s -> %s", sandbox, code, kwargs, rv)
        return rv

    def get_active_coupons( self, sandbox, pa=None, ga_codes=None, free=False ):
        """
        Return list of active coupons matching criteria
        """
        log.debug("Lookup coupons: %s, %s", pa, ga_codes)
        q = self.model.search_Q( pa, free )
        actives = self.filter( *q, sandbox=sandbox )
        if ga_codes:
            rv = []
            for active in actives.iterator():
                if intersection_comma_lists( ga_codes, active.account_codes ):
                    rv.append( active )
            return rv
        return list( actives )

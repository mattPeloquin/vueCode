#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayUsing manager
"""

from mpframework.common import log
from mpframework.foundation.tenant.models.base import TenantManager


class PayUsingManager( TenantManager ):

    def get_or_create( self, payto, apa, **kwargs ):
        """
        TBD - decide how to handle race conditions
        """
        (rv, _created) = super().get_or_create(
                    pay_to=payto, sandbox=apa.sandbox, account=apa.account )
        return rv

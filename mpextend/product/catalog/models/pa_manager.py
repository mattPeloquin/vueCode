#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PA represents a specific product offering
    (analogous to a SKU)
"""
from decimal import Decimal
from django.db.models import Q

from mpframework.common import log
from mpframework.foundation.tenant.models.base import TenantManager


class PaManager( TenantManager ):

    def pa_search( self, sandbox, sku ):
        """
        Get PA matching the sku or id, return None if no match
        """
        query = Q( sku__iexact=sku )
        try:
            query |= Q( id=int(sku) )
        except Exception:
            pass
        rv = self.mpusing('read_replica')\
                .filter( sandbox=sandbox )\
                .filter( self.model.available_Q() )\
                .filter( query )\
                .first()
        log.debug("SKU lookup: %s, %s -> %s", sandbox, sku, rv)
        return rv

    def lookup_queryset( self, sandbox ):
        """
        Provide list of options to autolookup (used in APA)
        """
        return self.get_available_pas( sandbox.pk )

    def create_obj( self, **kwargs ):
        """
        Create a default pa, filling in any info from agreement as needed
        Normally the PA is created in the admin UI.
        """
        unit_price = kwargs.pop( '_unit_price', 0 )
        if unit_price is not None:
            unit_price = Decimal( unit_price )
        pa = self.model( _unit_price=unit_price, **kwargs )
        pa.save()
        return pa

    def get_available_pas( self, sandbox_id, **filters ):
        """
        Get queryset of active PAs, with optional filtering
        """
        log.debug2("Lookup up pas: %s", sandbox_id)
        return self.filter( self.model.available_Q(), sandbox_id=sandbox_id, **filters )

    def get_purchase_pas( self, sandbox_id, **filters ):
        """
        Return LIST of PAs that require payment
        """
        rv = []
        filters['visibility'] = filters.get( 'visibility', 'A' )
        pas = self.get_available_pas( sandbox_id, **filters )
        for pa in pas.iterator():
            if not pa.access_no_payment:
                rv.append( pa )
        return rv

    def account_filter( self, pas, account ):
        """
        Filter a set of pas by account; if query set, force DB query to get list
        """
        rv = []
        for pa in list( pas ):
            if pa.visible_to_account( account ):
                rv.append( pa )
        return rv

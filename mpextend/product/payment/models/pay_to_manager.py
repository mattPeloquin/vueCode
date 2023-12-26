#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    PayTo manager
"""
from django.db import transaction
from django.db.utils import IntegrityError

from mpframework.common import log
from mpframework.foundation.tenant.models.base import TenantManager


class PayToManager( TenantManager ):

    def get_paytos( self, apa ):
        """
        Figure out who to pay based on the APA and available pay_to objects.
        Only one level of account, sandbox, provider is used.
        """
        # First check for an account seller
        pt = getattr( apa.account, 'pay_to', None )
        # Then check for sandbox
        if not pt:
            pt = getattr( apa.account.sandbox, 'pay_to', None )
        # Then check provider
        if not pt:
            pt = getattr( apa.account.sandbox.provider, 'pay_to', None )
        if pt:
            rv = list( pt.all() )
        return rv

    def get_or_create( self, payment_type, **kwargs ):
        """
        PayTos are unique for Sandbox/PaymentType combos, and are looked
        up by sandbox/type or service_account/type.
        """
        log.debug2("PayTo get_or_create: %s, %s", payment_type, kwargs)
        rv = None
        try:
            rv = self.get( payment_type=payment_type, **kwargs )
        except self.model.DoesNotExist:
            # Can only create a new PayTo if we have the sandbox
            sandbox = kwargs.get('sandbox')
            if sandbox:
                log.debug("Creating PayTo: %s, %s", payment_type)
                try:
                    with transaction.atomic():
                        rv = self.model( _provider=sandbox.provider,
                                    payment_type=payment_type,
                                    **kwargs )
                        rv.save()
                except IntegrityError:
                    rv = self.get( sandbox=sandbox, payment_type=payment_type )
        return rv


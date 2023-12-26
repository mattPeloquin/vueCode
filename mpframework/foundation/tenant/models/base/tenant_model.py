#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for tenant models
"""


class TenantBaseMixin:

    # Set by specialization to define field used for tenancy
    _tenancy_type = ''

    def __init__( self, *args, **kwargs ):
        # Add the tenancy key defined downstream to default admin requests
        self.select_related_admin = getattr( self, 'select_related_admin', () )
        self.select_related_admin += ( self._tenancy_type ,)
        super().__init__( *args, **kwargs )

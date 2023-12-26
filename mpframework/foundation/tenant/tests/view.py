#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for System items
"""

from django.urls import reverse

from mpframework.testing.framework import ViewTestCase
from mpframework.testing.utils import bh


class ViewTests( ViewTestCase ):

    def test_urls(self):

        self.l("Visitor tenant and provider urls")

        self.sandbox_init()
        self.get_url( '/user/terms', success_text='ROOT TERMS')
        self.get_url( '/user/privacy', success_text='Root privacy')
        self._common_tenant()
        self.get_url( bh('/ad/tenant/provider/1/'), fail=True )

        # Use specific urls for staff, since data for app_staff_urls_test
        # won't match up to the areas test users have tennancy for
        self.l("Staff and provider urls")

        self.login_staff()
        self._common_tenant( fail=False )
        self.get_url( bh('/ad/tenant/provider/1/'), fail=True  )
        self.get_url( bh('/ad/tenant/provider/11/'), fail=True  )
        self.get_url( bh('/ad/tenant/sandbox/'), fail=True  )

        self.login_owner()
        self._common_tenant( fail=False )
        self.get_url( bh('/ad/tenant/sandbox/') )
        self.get_url( bh('/ad/tenant/provider/11/') )
        self.get_url( bh('/ad/tenant/provider/1/'), fail=True  )
        self.get_url( bh('/ad/tenant/provider/12/'), fail=True  )
        self.get_url( bh('/ad/tenant/sandbox/40/'), fail=True  )

        self.l("Root tenant urls for sandbox 30")
        self.login_root( 30 )
        self._common_tenant()
        self.get_url( bh('/ad/tenant/sandbox/') )
        self.get_url( bh('/ad/tenant/provider/12/') )
        self.get_url( bh('/ad/tenant/sandbox/30/') )
        self.get_url( bh('/ad/tenant/provider/1/'), fail=True  )
        self.get_url( bh('/ad/tenant/provider/11/'), fail=True  )

        # Root should be able to see everything, so use introspection
        self.l("Root tenant urls for root site")
        self.login_root( 1, reset=True )
        self.app_root_urls_test('tenant')

    def _common_tenant( self, fail=True ):
        self.get_url( bh('/ad/tenant/sandbox/20/'), fail=fail )
        self.get_url( bh('/ad/tenant/sandboxcustom/20/'), fail=fail )


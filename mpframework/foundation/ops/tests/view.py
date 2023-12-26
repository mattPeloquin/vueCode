#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for ops
"""
from django.urls import reverse

from mpframework.testing.framework import ViewTestCase


class ViewTests( ViewTestCase ):

    def test_urls(self):

        self.l("Staff Ops URLs")
        self.login_staff()
        self._ops_views( fail=True )
        self._util_views()

        self.l("Root Ops URLs")
        self.login_root()
        self._ops_views()

        if self.test_level:

            self.l("Visitor and user ops URLs")
            self.sandbox_init()
            self._ops_views( fail=True )
            self._util_views( fail=True )
            self.login_user()
            self._ops_views( fail=True )
            self._util_views( fail=True )

            self.login_root( 30 )
            self._ops_views()

    def _util_views( self, fail=False ):

        self.l("Health")
        self.get_url('/mphealth', success_text='127.0.0.1', no_host=True)

        self.l("S3Direct")
        rv = self.fetch_post( reverse('upload_metadata'), {
            'dest': 'test',
            'name': 'DummyFile.mp4',
            'type': 'video/mp4',
            'size': 456,
            }, fail=fail )
        if not fail:
            self.assertTrue( 'DummyFile' in rv['object_key'] )
        self.post_url( reverse('upload_signature'), {
            'to_sign': 'DUMMY_SIGN',
            'datetime': '20190811T170620Z',
            }, fail=fail, success_text=False )

    def _ops_views( self, fail=False ):

        self.app_root_urls_test( 'ops', fail=fail )

        self.get_url( reverse('ops_dashboard'), fail=fail)

        # Need to do initialization on poller to test logging
        self.post_url( reverse('ops_logging'), fail=fail, data={
            'logging_debug': 3,
            'log_timing': 'on',
            'log_db': 'on',
            })

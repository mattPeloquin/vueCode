#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Plan app tests
"""
from django.urls import reverse

from mpframework.testing.framework import ModelTestCase
from mpframework.testing.framework import ViewTestCase
from mpframework.testing.utils import bh

from .models import UserPlan
from .models import GroupPlan


class ModelTests( ModelTestCase ):

    def test_plans( self ):
        user = self.login_user( 21 )

        up = UserPlan.objects.get_or_create( user )
        self.assertTrue( up.name )

        ga = user.account_user.primary_account.group_account
        gp = GroupPlan.objects.get_or_create( ga )
        gp._name = 'TestGP'
        gp.save()
        self.assertTrue( gp.name == 'TestGP')


class ViewTests( ViewTestCase ):

    def test_plans( self ):

        self.l("Visitor plan urls")
        self.sandbox_init()
        self._plan_urls( fail=True )

        self.l("User plan urls")
        self.login_user()
        self._plan_urls()

    def _plan_urls( self, fail=False ):

        self.app_staff_urls_test( 'plan', fail=fail )

        self.get_url( reverse('user_plans'), fail=fail )

        self.get_url( bh('/plan/admin_plans'), fail=fail )
        self.get_url( bh('/plan/admin_plans/99'), fail=True )

        rv = self.fetch_get( '/api/plan/plans', fail=fail )
        if not fail: self.assertTrue( 'user@acme.com' in str(rv['plans']) )

        rv = self.fetch_post( '/api/plan/tree_plan', {
            'action': 'ADD',
            'tree_id': 1002,
            'plan_id': 1,
            }, fail=fail )
        if not fail: self.assertTrue( rv )

        rv = self.fetch_get( '/api/plan/plans', fail=fail )
        if not fail: self.assertTrue( 1002 in rv['plans'][0]['nodes'] )

        rv = self.fetch_post( '/api/plan/tree_plan', {
            'action': 'REMOVE',
            'tree_id': 1002,
            'plan_id': 1,
            }, fail=fail )
        if not fail: self.assertTrue( rv )

        rv = self.fetch_get( '/api/plan/plans', fail=fail )
        if not fail: self.assertTrue( 1002 not in rv['plans'][0]['nodes'] )

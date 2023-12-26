#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for user content models and related application tests
"""

from mpframework.testing.framework import ModelTestCase
from mpframework.content.mpcontent.models import Tree

from ..models import ContentUser
from ..models import UserItem
from ..models import Badge


class ModelTests( ModelTestCase ):

    def test_user_item( self ):
        """
        Using ContentUser 25 with Sandbox 60, as they have no user_items
        and have Dev access to content
        """
        user = self.login_user()

        provider = user.provider
        sandbox = user.sandbox
        self.assertTrue( provider )
        self.assertTrue( sandbox )

        self.l("Creating new content for %s", provider)
        l1 = Tree( _provider_id=provider.pk, _name='Test Tree', workflow='P' )
        l1.save()
        l1.sandboxes.add( sandbox )
        self.assertTrue( l1 )

        badges = Badge.objects.filter( user_filter=user )

        self.l("Connecting user to content")
        cu = ContentUser.objects.get_contentuser( user )
        ui = cu.user_item( l1 )
        self.assertTrue( ui )
        self.assertFalse( ui.is_complete )

        self.assertTrue( cu.my_items_full )

        self.l("Adding progress info")
        ui.set_progress("TEST_DATA")
        self.assertTrue( ui.progress_data == "TEST_DATA" )
        self.assertTrue( ui.seconds_used >= 0 )
        self.assertTrue( ui.minutes_used >= 0 )

        self.l("Completing item")
        ui.complete()
        self.assertTrue( ui.is_complete and ui.completed )

        self.l("Adding feedback")
        ui.set_feedback( UserItem.FEEDBACK_FOUR )
        self.assertTrue( ui.feedback == UserItem.FEEDBACK_FOUR )
        ui.set_feedback( data={'VERSION': { 'Quality': 3, 'Comments': "Test Comment"} } )
        self.assertTrue( ui.feedback_data['VERSION']['Quality'] == 3 )
        self.assertTrue( ui.feedback_data['VERSION']['Comments'] == "Test Comment" )

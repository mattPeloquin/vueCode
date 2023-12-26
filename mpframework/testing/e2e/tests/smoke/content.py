#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    High-level tests focused on content types
"""

from mpframework.testing.e2e.tests.base import SystemTestCase
from mpframework.testing.e2e.blocks import ContentBlock


@SystemTestCase.register
class ContentSmokeTests( SystemTestCase ):

    def test_types( self ):
        """
        Make sure each content type can be created
        """
        self.owner.login()

        download = ContentBlock( self, type='file' )
        download.verify_portal()

        page = ContentBlock( self, type='protectedpage' )
        page.verify_portal()

        pdf = ContentBlock( self, type='pdf' )
        pdf.verify_portal()

        video = ContentBlock( self, type='video' )
        video.verify_portal()

        audio = ContentBlock( self, type='audio' )
        audio.verify_portal()

        embed = ContentBlock( self, type='embed' )
        embed.verify_portal()

        link = ContentBlock( self, type='proxylink' )
        link.verify_portal()

        app = ContentBlock( self, type='proxyapp' )
        app.verify_portal()

        quiz = ContentBlock( self, type='quiz' )
        quiz.verify_portal()

        item = ContentBlock( self, type='portalitem' )
        item.verify_portal()

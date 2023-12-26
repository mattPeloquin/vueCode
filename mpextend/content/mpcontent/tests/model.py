#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for content models and related application tests
"""
import os
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from mpframework.testing.framework import ModelTestCase

from ..models import ProxyApp
from ..models import Audio
from ..models import Embed
from ..models import ProxyLink
from ..models import LiveEvent
from ..models import LmsItem
from ..models import ProtectedPage
from ..models import Quiz
from ..models import Video
from ..models import PortalItem


class ModelTests( ModelTestCase ):

    def test_content(self):
        user = self.login_user()

        self.l("Create content objects")
        apps = ProxyApp.objects.filter( user_filter=user )
        audios = Audio.objects.filter( user_filter=user )
        embeds = Embed.objects.filter( user_filter=user )
        links = ProxyLink.objects.filter( user_filter=user )
        event = LiveEvent.objects.filter( user_filter=user )
        lmsitems = LmsItem.objects.filter( user_filter=user )
        pages = ProtectedPage.objects.filter( user_filter=user )
        quizzes = Quiz.objects.filter( user_filter=user )
        videos = Video.objects.filter( user_filter=user )
        pi = PortalItem.objects.filter( user_filter=user )
        self.assertTrue( apps and audios and embeds and links and event and
                lmsitems and pages and quizzes and videos and pi )

        self.l("Add LMS")
        with open( os.path.join( settings.MP_TEST_FOLDERS_PACKAGES[0], 'LMSTEST_Battle.zip' ),
                   'rb' ) as test_zip:
            file_data = UploadedFile( file=test_zip, size=os.path.getsize(test_zip.name) )
            new_lms = LmsItem.objects.create_obj( sandbox=user.sandbox,
                            name='Test LMS Item1', tag='TestLMSItem1',
                            file_name='TestZip.zip', file_data=file_data )
            self.wait_for_threads()
        self.assertTrue( new_lms.tag == 'TestLMSItem1' )


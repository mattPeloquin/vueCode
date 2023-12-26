#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for content models and related application tests
"""

import os
import time

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from mpframework.testing.framework import ModelTestCase
from mpframework.testing.framework import requires_normal_db

from ..models import Package
from ..models import PackageRoot


class ModelTests( ModelTestCase ):

    def test_package(self):

        # Testing package name manipulation; this file don't exist
        run_name = Package._run_name("test/archive/test path.zip")
        self.assertTrue( "test path" in run_name )

        # Get package from test data
        package = Package.objects.get( id=1 )
        self.l( package )
        self.l( package.archive_name )
        self.assertTrue( package._is_test_fixture )
        self.assertTrue( package._launch_file )
        self.assertTrue( package._runpath() )
        self.assertTrue( package._runurl )

        # Test the metrics to identify the number of users using
        all_packages = Package.objects.filter()
        for package in all_packages:
            if package.pk == 1:
                self.assertTrue( package.user_count == 0 )
            elif package.pk == 2:
                self.assertTrue( package.user_count == 2 )
            else:
                self.assertTrue( package.user_count == 0 )

        p14 = Package.objects.get( pk=14 )
        self.assertTrue( p14 )

        self.assertTrue( package.lms_type == 'A' )

    @requires_normal_db
    def test_create(self):
        """
        This has side effects in the file system and uses threads can't use in-memory DB
        Have to do some sleeping to let threads work.
        Expanded files are left in the work folder
        """
        provider = self.get_user( id=11 )

        self.l("Creating package from fake upload file")
        with open( os.path.join(settings.MP_TEST_FOLDERS_PACKAGES[0], 'LMSTEST_Battle.zip'),
                   'rb' ) as test_zip:
            file_data = UploadedFile( file=test_zip, size=os.path.getsize(test_zip.name) )
            new_root = PackageRoot.objects.create(
                                "TestPackage",
                                file_data,
                                'S',        # Storyline package type
                                'S',        # Scorm LMS type
                                provider
                                )
            new_package = new_root.package
            # This is dicey, as separate thread doing the unpacking; depending
            # on our environment this could take awhile before we can get url
            seconds_waited = 0
            while not new_package.run_ready and seconds_waited < 10:
                self.l("Waiting for the mount thread to finish")
                time.sleep( 2 )
                seconds_waited += 2
            self.assertTrue( new_package.url )
            # Sleep a bit to let thread die so we can clean up DB
            time.sleep( 1 )

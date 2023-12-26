#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Wraps the upload/storage/mounting of uploaded package files

    Packages are normally zipped Scorm or TinCan files, but can also be other
    collections of zipped files or single files like movies.

    The conceptual idea is once a package zip file is loaded into the system, it will be
    there for all time as an archive.
    When requested, if not already "mounted", archives are expanded into the appropriate
    protected location -- this can be done as loaded or lazily depending on config.
    As long as the archive path in the DB points to a valid location, a server instance
    will try to mount the archive if it hasn't already been done.

    Various deployment options for storing archive and protected package files
    in different places (S3, local, etc.) are supported.

    There is special-case support for package test fixtures to support efficient dev

    Package mounting occurs using MPF per-sever asynchronous signals.
    This is done vs. distributed task queue because mounting needs to run
    immediately against the server instance that has the files stored locally.
    It is also expected to be relatively low-volume compared to other system events.

    Launch files

        Different scorm tools have different launch files. The package doesn't
        care about any specialized behavior of these tools, just the name of the
        launch file. These files are reasonably standardized, so try to pick
        them up automatically for the most popular tools, while also supporting
        manual override.

    Package folders are organized by provider/sandbox, but the package class does not have
    DB connections to providers.
"""
import os
import shutil
from zipfile import ZipFile
from zipfile import BadZipfile
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from mpframework.common import _
from mpframework.common import log
from mpframework.common import CHAR_LEN_PATH
from mpframework.common.aws import s3
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import run_queue_function
from mpframework.common.utils import join_urls
from mpframework.common.utils import join_paths
from mpframework.common.utils.file import create_file_from_post
from mpframework.common.utils.file import create_local_folder
from mpframework.common.deploy.server import mp_shutdown
from mpframework.common.logging.timing import mpTiming
from mpframework.foundation.tenant.models.base.provider import ProviderModel
from mpextend.user.usercontent.models import UserItem

from .manager import PackageManager


_package_retry_time = settings.MP_CONTENT.get( 'LMS_PACKAGE_RETRY', 2 )
_launch_config = settings.MP_CONTENT['LMS_PACKAGE_LAUNCH_FILES']


class Package( ProviderModel ):
    """
    Wraps a path to a package archive and unzipped package folder
    Hides whether files are being hosted on AWS or not

    The Package class does NOT use mpFileProtectedField for any file management
    """

    # Connect back to package's root
    # There should always be a package root, but do not enforce in the
    # DB to make maintenance tasks easier
    package_root = models.ForeignKey( 'lms.PackageRoot', models.CASCADE,
                                      null=True, blank=True,
                                      related_name='packages' )

    # Name of the archived zip file
    archive_name = models.CharField( max_length=CHAR_LEN_PATH )

    # Relative path to the location of files to be run
    run_name = models.CharField( default='', blank=True,
                                    max_length=CHAR_LEN_PATH )

    # Flag for handling lazy unzipping prevention of remounting
    mounting = models.BooleanField( default=False )

    # Ready means unzipped and transferred to S3 origin)
    run_ready = models.BooleanField( default=False )

    # Allow bypassing launch auto-detect, forcing use of custom launch file
    # Placebo entries for Captivate and Storyline, which are same as auto
    PACKAGE_TYPE = (
        ('A', _("Auto detect")),
        ('C', _("Captivate")),
        ('S', _("Storyline")),
        ('O', _("Other")),
        )
    package_type = models.CharField( max_length=1, choices=PACKAGE_TYPE,
                                        default='A', blank=False )

    # The type of LMS standard the package is published to support
    LMS_TYPE = (
        ('A', _("Auto detect")),
        ('S', _("Scorm")),
        ('T', _("xAPI / TinCan")),
        ('O', _("Other")),
        )
    lms_type = models.CharField( max_length=1, choices=LMS_TYPE, default='A', blank=False )

    # File used to start package, which can be set automatically or manually
    launch_file = models.CharField( default='', blank=True, max_length=CHAR_LEN_PATH )

    objects = PackageManager()

    select_related_admin = ( '_provider', 'package_root', 'package_root__current' ,)

    lookup_fields = ( 'id__iexact', 'run_name__icontains' )

    def __str__( self ):
        # Should only be seen in root Admin
        return "pkg({}){}".format( self.pk, self.archive_name[:40] )

    def _clone_file_data( self, obj ):
        """
        Make cloning use the archive path, which is not stored in a file field
        """
        rv = { 'archive': {
                    'bucket': 'protected',
                    'source': obj.archive_path,
                    'target': self.archive_path,
                    }
                }
        log.debug("Package archive clone: %s -> %s", self, rv)
        return rv

    #--------------------------------------------------------------------

    @property
    def archive_path( self ):
        return join_paths( self.package_root.protected_storage_package, self.archive_name )

    @property
    def url( self ):
        """
        Return URL for running the package
        If the package is not ready, return None to indicate it is either being mounted
        or is in an inaccessible state
        """
        if self.run_ready:
            return self._runurl

        log.info("HEAL - Package not ready, mounting archive: %s", self.archive_name)
        self.mount_archive()

    @property
    def user_count( self ):
        """
        Count the number of users on this version
        """
        return UserItem.objects.filter( item_version=self.pk ).count()

    """--------------------------------------------------------------------
        Package file upload/unzip/mount management

        ZIP file is loaded to S3 (or local area) either directly or via
        normal post. The mounting happens by copying archive to a working
        folder to unzip, and then LMS files are moved to locations.
        This supports both production and local dev cases.
    """

    def write_archive( self, file_data ):
        """
        For non-direct upload of LMS zip file, take the upload file data from the
        POST request, place into local file, and then upload to S3.
        """
        local_path = create_file_from_post( file_data, self._local_archive_path )
        s3.upload_protected( local_path, self.archive_path )

    def mount_archive( self ):
        """
        Unzip package archive file and move to protected serving location.
        """
        # HACK - handle text fixtures outside normal mounting
        if self._is_test_fixture:
            if self._test_fixture_ready():
                return

        # If mounting is already in progress, let it finish
        if self.mounting:
            log.info("Package still mounting, skipping mount request: %s",
                        self.archive_name)
            return
        self.mounting = True
        self.save()
        run_queue_function( _mount_archive, self.provider, my_priority='HS',
                    package_id=self.pk )

    def _mount_archive( self ):
        """
        Download archive to server, unzip it, then push the pieces back up
        """

        # Get file from download location; if this fails nowhere to go
        local_package = self._download_package()
        if not local_package:
            # HACK - the package may be getting copied to S3, try once more
            mp_shutdown().wait( _package_retry_time )
            local_package = self._download_package()
            if not local_package:
                log.warning("Error in Package download, ending mounting process: %s",
                                self.archive_name)
                self.run_ready = False
                self.mounting = False
                self.save()
                return

        # Use local protected folder for unzipping files if necessary. The files can
        # then be uploaded to S3 or hosted directly
        local_expand_path = self._local_run_name
        create_local_folder( local_expand_path )

        log.info2("MOUNTING PACKAGE: %s\n  local_expand: %s\n path: %s, run url: %s",
                local_package, local_expand_path, self._runpath(), self._runurl )

        # Try to unzip the file
        if not self._unzip_to_run_location( local_package, local_expand_path ):

            # If this isn't a zip file, try to push the file from the archive location to protected,
            # which will fail if local protected hosting is set, in which case the
            # file should be copied from archive to protected location
            if self._push_to_s3( local_package, self.archive_name ):
                log.debug("Package not zip file, pushed to S3: %s -> %s", local_package, self.archive_name)
            else:
                log.debug("Package not zip file, local copy: %s -> %s", local_package, local_expand_path)
                shutil.copy( local_package, local_expand_path )

        self._set_launch_type( local_expand_path )

        # Clean the uploaded file off the local server (don't kill test fixtures)
        if not self._is_test_fixture:

            log.debug("Removing local package upload file: %s -> %s", self, local_package)
            os.remove( local_package )

            log.debug("Removing local package unzipped files: %s -> %s", self, local_expand_path)
            try:
                shutil.rmtree( local_expand_path )
            except Exception:
                log.exception("Exception removing unzipped package file: %s -> %s", self, local_expand_path)

        # Mark the package as ready for use
        self.run_ready = True
        self.mounting = False
        self.save()

    def _set_launch_type( self, files_path ):
        """
        Auto-detect and set the launch file if needed
        """
        log.debug("Auto-detecting package launch file: %s -> %s", self, files_path)

        for lms_type, launch_files in _launch_config.items():

            if self.launch_file:
                log.debug("Package set launch file and type: %s -> %s, %s", self, self.lms_type, self.launch_file)
                return

            if self.lms_type in ['A', lms_type]:
                for file in launch_files:
                    log.debug2("Checking for launch file: %s -> %s, %s", self, lms_type, file)
                    if os.path.exists( join_paths( files_path, file ) ):
                        self.lms_type = lms_type
                        self.launch_file = file
                        break

        log.info("No launch file set during package mounting: %s", self)

    def _download_package( self ):
        """
        Tries to download package from S3 for expansion (or handle test fixtures in dev)
        Returns the local path to package if successful
        """
        if self._is_test_fixture:
            log.debug("PACKAGE mounting test fixture: %s", self)
            # TEST HACK - In the test fixture scenario, file already exists locally on the server,
            # so skip download archive step and expand from test fixture location
            # This is a divergence in test path but that gap will be covered by automated testing
            # that uploads packages like a staff user would
            local_path = self._test_fixture_archive()
        else:
            local_path = self._local_archive_path
            local_folder, _file = os.path.split( local_path )

            # If using S3, bring file down to the local server
            s3key = s3.protected_bucket()
            if s3key:
                try:
                    s3key.key = self.archive_path
                    log.debug("PACKAGE download: %s -> %s", s3key.key, local_path)

                    create_local_folder( local_folder )

                    with open( local_path, 'wb') as local_file:
                        s3key.get_contents_to_file( local_file )

                except Exception as e:
                    log.info2("Problem downloading package from S3: %s -> %s => %s",
                                s3key.key, local_path, e )
                    os.remove( local_path )
                    local_path = None

            # if not using S3, file is already in place on local server
            else:
                log.debug("PACKAGE LOCAL upload: %s", self)

        return local_path

    def _unzip_to_run_location( self, local_path, protected_path ):
        """
        Locally unzip package and move the files up to S3
        Returns false if the file is not a valid zip file
        """
        try:
            # Best way to test for valid zip is to open as zip and test
            zip = ZipFile( local_path, 'r' )
            valid_zip = zip.testzip() is None
        except BadZipfile:
            valid_zip = False
        if not valid_zip:
            return False

        # Unzip files into the local location and then push to S3 if needed
        log.debug("UNZIPPING, then uploading package files: %s => %s => S3", local_path, protected_path)

        # Avoid use of extractall to guard against malformed zip attacks
        for item in zip.namelist():
            path = join_paths( protected_path, str(item) )
            if item.endswith('/'):
                create_local_folder( path )
            else:
                log.debug2("Extracting file: %s", item)
                zip.extract( item, protected_path )

                # If S3 not enabled, this fails, and files will be hosted from server
                self._push_to_s3( path, item )

        zip.close()
        return True

    def _push_to_s3( self, path, filename='' ):
        return s3.upload_protected( path, self._runpath( filename ) )

    def _test_fixture_archive( self ):
        """
        TEST HACK -- find the fixture folder this archive is from
        """
        for fixture_path in settings.MP_TEST_FOLDERS_PACKAGES:
            fixture_archive = join_paths( fixture_path, self.archive_name )
            try:
                with open( fixture_archive ):
                    log.debug2("   test fixture found: %s", fixture_archive)
                    break
            except IOError:
                log.debug2("   test fixture does not exist: %s", fixture_archive)
                fixture_archive = None
        if not fixture_archive:
            raise Exception("TEST PACKAGE NOT FOUND: %s\n%s" %
                    (self.archive_name, settings.MP_TEST_FOLDERS_PACKAGES))
        return fixture_archive

    #--------------------------------------------------------------------

    @staticmethod
    def _run_name( archive_name ):
        """
        Return the url for launching the package

        Static method to support use in manager

        Use a strong unique name here because the text of this path can be visible
        in the URL used to launch the package
        """
        # FUTURE -- Hardcoded assumptions about zip, may need to expand later
        run_name = archive_name[:-4] if archive_name.endswith('.zip') else archive_name
        return run_name

    @property
    def _runurl( self ):
        # Full URL necessary to launch the package
        rv = join_urls( self.run_name, self._launch_file )
        log.debug2("Package _runurl: %s", rv)
        return rv

    def _runpath( self, filename='' ):
        """
        Relative path necessary to run package. If file is provide, it is appended
        """
        rv = join_paths( self.package_root.protected_storage_lms, self.run_name, filename )
        log.detail3("Package _runpath: %s", rv)
        return rv

    @property
    def _launch_file( self ):
        """
        Every package has one file used to launch it. This should be set up when
        then package is mounted, but can be overridden.
        If none is provided, use the name of the archive itself
        """
        rv = self.launch_file if self.launch_file else self.archive_name
        log.detail3("Package launch_file: %s", rv)
        return rv

    @property
    def _local_run_name( self ):
        # Location where lms content is hosted
        return join_paths( settings.MP_FOLDER_PROTECTED_LOCAL,
                    self.package_root.protected_storage_lms, self.run_name )
    @property
    def _local_archive_path( self ):
        # Location where an upload file is placed (if not uploaded directly)
        return join_paths( settings.FILE_UPLOAD_TEMP_DIR, self.archive_name )

    #-----------------------------------------------------------------------
    # TEST HACK - Support test fixture packages

    @property
    def _is_test_fixture( self ):
        """
        HACK - HARD CODED NAME DEPENDENCY TO TEST FIXTURE FILE NAMES
        In normal uploads, the archive file will have been uploaded to S3 or
        to local archive folder for local dev.
        Test fixture files are a special case, because we want them checked in with
        test data, so they will start out in the fixtures folder and not be created and
        uploaded like a package file normally would be.
        """
        return settings.MP_TEST_USE_FIXTURES and self.archive_name.startswith('LMSTEST_')

    def _test_fixture_ready( self ):
        s3key = s3.protected_bucket()
        if s3key:
            s3key.key = join_urls( self.package_root.protected_storage_lms, self.run_name )
            exists = s3key.exists()
            log.info("S3 test package: %s  mounted = %s", s3key.key, exists)
        else:
            local_run_name = join_paths( self._local_run_name )
            exists = os.path.exists( local_run_name )
            log.info("Local test package: %s  mounted = %s", local_run_name, exists)

        if not exists:
            self.run_name = self._run_name( self.archive_name )
            self.save()
            log.debug("Attempting to mount TEST PACKAGE: %s", self.run_name)

        return exists


@mp_async
def _mount_archive( **kwargs ):
    """
    Async mounting of package in spooler
    """
    log.debug("Executing mount archive task: %s", kwargs)
    t = mpTiming()
    package_id = kwargs.pop('package_id')

    package = Package.objects.get( id=package_id )
    package._mount_archive()

    log.info("<= %s Package mount complete: %s items", t, package)

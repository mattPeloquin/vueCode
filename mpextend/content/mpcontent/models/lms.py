#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    LmsItems are Content items for LMS packages
    The lms app includes specialized support for LmsItems
"""
from django.db import models
from django.conf import settings
from django.db.utils import OperationalError

from mpframework.common import log
from mpframework.common.events import sandbox_event
from mpframework.common.cache.stash import stash_method_rv
from mpframework.common.delivery import DELIVERY_COMP_LMS
from mpframework.common.utils import join_urls
from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager
from mpextend.content.lms.models import PackageRoot


class LmsItemManager( ItemManager ):

    def create_obj( self, **kwargs ):

        # If file_name is passed, this is from upload dialog, so setup package
        # If file data is passed, upload was in post, otherwise it was direct
        file_name = kwargs.pop( 'file_name', None )
        if file_name:
            options = {}
            lms_type = kwargs.pop( 'lms_type', None )
            if lms_type: options['lms_type'] = lms_type
            package_type = kwargs.pop( 'package_type', None )
            if package_type: options['package_type'] = package_type

            package_root = PackageRoot.objects.create_obj(
                                    _provider=kwargs['sandbox'].provider,
                                    file_name=file_name,
                                    file_data=kwargs.pop( 'file_data', None ),
                                    **options )

        # Otherwise, package root will be set as part of cloning
        else:
            package_root = None

        lms = super().create_obj( package_root=package_root, **kwargs )
        return lms


class LmsItem( BaseItem ):
    """
    LmsItems represent LMS items as Content while adding support from
    the LMS app for package management.
    LMS packages are ZIP files that require special handling and have the
    potential to hold significant state in their resume data.
    LmsItem uses LMS packages to manage multiple package versions.
    """

    # LmsItems manage Package file versions through a PackageRoot.
    # Packages may change over time, but there should always one current package
    # This is NOT enforced by DB to make maintenance tasks easier
    package_root = models.ForeignKey( PackageRoot, models.SET_NULL,
                null=True, blank=True, related_name='lms_items' )
    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"LMS package"

    objects = LmsItemManager()
    select_related_admin = BaseItem.select_related + (
                'package_root', 'package_root__current' )
    access_type = 'lms'

    def _type_name_LmsItem( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def _can_complete_LmsItem( self ):
        # DOWNCAST METHOD
        return True

    def clone( self, **kwargs ):
        """
        Need to clone package for LMS content
        """
        new_lms = super().clone( **kwargs )
        new_root = self.package_root.clone( _provider=new_lms.provider )
        new_lms.package_root = new_root
        new_lms.save()
        return new_lms

    def get_access_url( self, request, **kwargs ):
        """
        Use the protected pass-through url prefix to allow nginx to
        serve some file types without checking with Django, and force
        use of LMS delivery mode to handle cross-domain issues
        """
        kwargs['url_prefix'] = settings.MP_URL_PROTECTED_PASS
        kwargs['default_mode'] = DELIVERY_COMP_LMS
        return super().get_access_url( request, **kwargs )

    def package_url( self, version=None ):
        """
        Gets the url to launch a package version (defaults to current)
        """
        url = ''
        try:
            if version:
                package = self.package_root.get_package( version )
                if package:
                    url = package.url
            if not url:
                url = self.package_root.current.url
        except OperationalError:
            # Most likely DB connection needs reset, let caller manage
            raise
        except Exception as e:
            if settings.MP_DEV_EXCEPTION:
                raise
            log.warning("Problem loading LMS package %s -> %s", self, e)
        return join_urls( self.protected_storage_path, url )

    @property
    @stash_method_rv
    def protected_storage_path( self ):
        return self.package_root.protected_storage_lms

    @property
    def version( self ):
        """
        Store the current package ID in version, allowing it to be referenced
        """
        return self.package_root.current.pk

    def update_package( self, file_name, file_data, package_type, lms_type, user ):
        """
        Create new package file for this lms item
        This will be used for any new user items that are started.
        ContentUserItems in progress will still use previous package files
        This approach preserves package suspend state for each student
        """
        sandbox_event( user, 'content_lms_update', self, file_name )

        if self.package_root:
            self.package_root.new_package( file_name=file_name, file_data=file_data,
                                           package_type=package_type, lms_type=lms_type )
        else:
            # Support healing if package root is not available
            self.package_root = PackageRoot.objects.create_obj( _provider = self.provider,
                                    file_name=file_name, file_data=file_data,
                                    package_type= package_type, lms_type=lms_type )
            self.save()

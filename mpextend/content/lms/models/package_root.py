#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Wrap connection of packages to LMS items
"""
from django.db import models

from mpframework.common import log
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.foundation.tenant.models.base import ProviderModel

from .package import Package


class PackageRootManager( TenantManager ):

    def create_obj( self, **kwargs ):
        """
        Package roots manage package lifetime, creating a new package root
        entails creating a new current package, while when cloning the new
        root is created first, and then the current package is cloned and added
        """
        package_root = PackageRoot( _provider=kwargs['_provider'] )
        package_root.save()
        log.debug("CREATED PackageRoot: %s", package_root)

        if kwargs.get( 'file_name' ):
            package = Package.objects.create_obj( package_root=package_root, **kwargs )
            package_root.current = package
            package_root.save()

        return package_root


class PackageRoot( ProviderModel ):
    """
    Connects packages to LMS items

    Packages may be updated over time, AND support keeping
    user references to older packages.
    So a collection of Packages could be associated with a given LMS item,
    which the PackageRoot is responsible for abstracting.
    """

    # The current package for this collection
    # Allow this to be null primarily for creation of new recrod
    current = models.ForeignKey( Package, models.SET_NULL,
                                         null=True, blank=True,
                                         related_name='current_roots' )

    objects = PackageRootManager()
    select_related = ( 'current' ,)

    def __str__( self ):
        # Should only be seen in root admin
        return "prt({})-{}".format( self.pk, self.current )

    def clone( self, **kwargs ):
        """
        Cloning only takes the current package and resources; older versions are ignored
        """
        new_root = super().clone( **kwargs )
        new_package = self.current.clone( package_root=new_root )
        new_package.mount_archive()
        new_root.current = new_package
        new_root.save()
        return new_root

    @property
    def protected_storage_package( self ):
        # This is the path where LMS zip files are stored
        return self.provider.policy.get( 'storage.lms_packages',
                                         self.provider.protected_storage_path )
    @property
    def protected_storage_lms( self ):
        # This is the path where LMS files are expanded to
        return self.provider.policy.get( 'storage.lms',
                                         self.provider.protected_storage_path )
    @property
    def all_packages(self):
        return self.packages.all()

    @property
    def package_count( self ):
        return self.packages.count()

    def get_package( self, package_id ):
        return Package.objects.get_quiet( _provider_id=self._provider_id, id=package_id )

    def new_package( self, **kwargs ):
        """
        Create the new package and make it default to provide for new lms items,
        while storing reference to any existing package.
        The old package version remains linked to users, need to force update
        on package to align lms item with new package
        """
        self.current = Package.objects.create_obj( package_root=self, **kwargs )
        self.save()
        return self.current

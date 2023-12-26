#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Public file uploads
"""
from django.db import models

from mpframework.common import constants as mc
from mpframework.common.model.fields import mpFileFieldPublic
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.foundation.tenant.models.base import TenantManager


class PublicFile( SandboxModel ):
    """
    Upload of files for direct link public download, to support hosting
    resources used for custom sites.

    Unlike content resources, these file names are not mangled, so
    they can be shared and replaced in one location.

    The link is direct to CDN vs. through an MPF url because indirection
    is not really needed, and no need to add unnecessary server hits.

    FUTURE - consider allowing drop-down selection of public images
    as an option for file upload for both content and inside editors.
    """

    _name = models.CharField( blank=True, max_length=mc.CHAR_LEN_UI_DEFAULT,
                db_column='name' )

    filename = mpFileFieldPublic()

    class Meta:
        app_label = 'sitebuilder'

    objects = TenantManager()

    def __str__( self ):
        if self.dev_mode:
            return "pf({},s:{}){}".format( self.pk, self.sandbox_id, self.filename )
        return self.name

    @property
    def name( self ):
        return self._name or self.filename

    def public_storage_name( self, storage_name ):
        """
        Disable name mangling to allow overwrite of existing site files with same name
        """
        return storage_name

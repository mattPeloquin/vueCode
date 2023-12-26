#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Store old values when changes made to selected fields

    The goal of this mechanism is to provide backup / undo functionality
    for human error on effort-intensive field content.

    FUTURE - convert to per-row change, tie in with undo
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from mpframework.common import constants as mc
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.foundation.tenant.models.base import TenantManager


class FieldChange( SandboxModel ):
    """
    Works with tenant base classes to provide undo functionality

    FUTURE - FieldChange just list for now, but Generic key so could support undo later
    """

    # The user that made the change
    user = models.ForeignKey( 'mpuser.mpUser', models.SET_NULL,
                              blank=True, null=True, related_name='field_changes' )

    # Model change was made to
    ctype = models.ForeignKey( ContentType, models.SET_NULL,
                blank=True, null=True, db_column='content_type_id' )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey( 'ctype', 'object_id' )

    # Field name (for programatic undo)
    field = models.CharField( max_length=mc.CHAR_LEN_UI_LONG )

    # Descriptive metadata (for manual browsing)
    desc = models.CharField( max_length=mc.CHAR_LEN_UI_LONG, blank=True )

    # The old field value is stored as some sort of text format
    # This functionality is most important for large text fields, but
    # can be used for other values by converting into YAML or JSON
    value = models.TextField()

    objects = TenantManager()

    def __str__( self ):
        return "{} {}({})".format( self.user, self.ctype, self.field )

#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Link mpUser to an SSO source.

    SSO is only supported for customer users.
    The SSO source does not know about MPF tenancy, so the
    same username in an SSO source may be shared across
    multiple sandboxes.
"""
from django.db import models

from mpframework.common import log
from mpframework.common.model import BaseModel
from mpframework.common.model import BaseManager
from mpframework.user.mpuser.models import mpUser

from .source import SsoSource


class UserSSO( BaseModel ):
    """
    Matches a customer user (with one sandbox)
    """

    # Each user can have ONE SSO user source
    user = models.OneToOneField( mpUser, models.CASCADE,
                related_name='sso_user' )
    source = models.ForeignKey( SsoSource, models.CASCADE,
                related_name='sso_users' )

    objects = BaseManager()

    select_related = ( 'user' ,)
    select_related_admin = select_related

    def __str__( self ):
        if self.dev_mode:
            return "ssou({}){}".format( self.pk, self.user )
        return self.user.email

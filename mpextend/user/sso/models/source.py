#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    "Source" for SSO authentication, which can be an
    OAUTH "Authorization server" or SAML IDP (Indentity Prodvier)
"""
from django.db import models

from mpframework.common import log
from mpframework.common.model import BaseModel
from mpframework.common.model import BaseManager
from mpframework.common.model.fields import YamlField

from ..sso_types import SOURCE_TYPES


class SsoSource( BaseModel ):
    """
    Each instance is an SSO identity source.

    MPF assumes source uses email for authentication and the source will provide
    hosted identity access like AWS Cognito.
    """

    # The SSO source type can change configuration and logic
    source_type = models.CharField( max_length=16,
                choices=[ (n, v['name']) for n, v in SOURCE_TYPES.items() ] )
    source_config = YamlField( null=True, blank=True )

    objects = BaseManager()

    def __str__( self ):
        if self.dev_mode:
            return "ssos({}){}".format( self.pk, self.source_type )
        return self.source_type

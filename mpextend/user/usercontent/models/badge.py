#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Badges support content gamification, certificates, etc.
"""
from django.db import models

from mpframework.common import constants as mc
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.foundation.tenant.models.base import SandboxModel
from mpframework.content.mpcontent.tags import ContentTagMatchMixin
from mpframework.content.mpcontent.models import BaseContentFields
from mpframework.content.mpcontent.models.base.files import create_mpfile_mixin


_CertificateFileMixin = create_mpfile_mixin('certificate_file')


class Badge( _CertificateFileMixin, ContentTagMatchMixin,
                BaseContentFields, SandboxModel ):
    """
    Badge content represents any certificate, etc. that is tied via
    usercontent to represent a user accomplishment.

    Unlike other content which users control access to, "access"
    to badge content (e.g., certificate) is designed to be granted
    programmatically.

    Although based on some shared content fields, Badges are not shared
    across Sandboxes and do not use workflow as this would increase
    complexity for marginal use cases.

    FUTURE -- provide support for printable certificate
    """

    # Optional content tag that can be used both to group badges
    # and limit their availability through APA licensing
    badge_tag = models.CharField( db_index=True, max_length=mc.CHAR_LEN_UI_CODE,
                                  blank=True, verbose_name=u"Badge code" )

    # These types are used to drive programatic behavior
    COMPLETION = (
        ('item_complete', u"Item completion"),
        ('tree_complete', u"Collection completion"),
        )
    completion = models.CharField( max_length=16, blank=False,
                                   choices=COMPLETION, default='tree_complete' )

    class Meta:
        verbose_name = u"Badge"

    objects = TenantManager()

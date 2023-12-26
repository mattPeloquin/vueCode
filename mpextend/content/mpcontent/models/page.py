#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    ProtectedPage has protected HTML content only shown in viewer.
"""
from django.db import models
from django.conf import settings

from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager


class ProtectedPage( BaseItem ):
    """
    Holds HTML content presented in a single page
    """

    # The protected page content
    # This HTML is only available once access is provided
    html = models.TextField( blank=True )

    # Try to disable printing of the content page?
    allow_print = models.BooleanField( default=False )

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Web page"

    objects = ItemManager()

    access_type = 'page'
    content_fields = ['html']

    def _type_name_ProtectedPage( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def save( self, *args, **kwargs ):
        self.update_content_rev()
        super().save( *args, **kwargs )

    def get_access_url( self, request, **kwargs ):
        """
        Use the protected pass-through url prefix to allow nginx to
        serve some file types without checking with Django
        """
        kwargs['url_prefix'] = settings.MP_URL_PROTECTED_PASS
        return super().get_access_url( request, **kwargs )

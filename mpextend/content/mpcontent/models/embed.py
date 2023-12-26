#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    HTML content embed

    Unlike the normal content page, this will allow scripting, etc.
    to be inserted on a displayed content page.
"""
from django.db import models

from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager


class Embed( BaseItem ):
    """
    Support HTML displayed in content iframe - no assumptions are made about
    HTML and scripting other than it must split between header and body groups.
    May be used to embed external videos, external quizzes or other content,
    or for self-contained content compiled from other sources.

    Unlike proxyied links, any external links that aren't secured will be
    visible to someone looking at browser debug.
    """

    # HTML and scripting to inject
    head = models.TextField( blank=True )
    body = models.TextField( blank=True, db_column='html' )

    # Add sandbox style
    add_style = models.BooleanField( default=False )

    # Option to process head and body as MPF templates
    head_template = models.BooleanField( default=True )
    body_template = models.BooleanField( default=False )

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Web embed"

    objects = ItemManager()

    access_type = 'embed'

    def _type_name_Embed( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def save( self, *args, **kwargs ):
        super().save( *args, **kwargs )

#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Quiz builder
"""

from mpframework.common.model.fields import YamlField
from mpframework.content.mpcontent.models import BaseItem
from mpframework.content.mpcontent.models import ItemManager


class Quiz( BaseItem ):
    """
    Convenience wrapper for JS quizzes that converts YAML into
    JSON and loads JS quiz framework
    """

    # Add proxy options for credentials, URL mappings, response fixup, etc.
    content = YamlField( null=True, blank=True )

    class Meta:
        app_label = 'mpcontent'
        verbose_name = u"Quiz"

    objects = ItemManager()

    access_type = 'quiz'
    content_fields = ['content']

    def _type_name_Quiz( self ):
        # DOWNCAST METHOD
        return self._meta.verbose_name_raw

    def save( self, *args, **kwargs ):
        self.update_content_rev()
        super().save( *args, **kwargs )

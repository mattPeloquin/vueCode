#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared content tag matching model functionality, which is
    MPF's mechanism for matching content to licenses and other
    groupings defined by user tag naming conventions.
"""
from django.db import models
from django.conf import settings

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.tags import tag_match
from mpframework.common.tags import tags_Q
from mpframework.common.cache import stash_method_rv
from mpframework.common.utils.strings import comma_tuple

from .models import BaseItem
from .models import Tree
from .utils import content_dict


def tag_code_help( intro="Add" ):
    return( u"{} content with comma-separated license tags.<br>"
            "Matched <b>collections include their content</b>.<br>"
            "Use <b>*</b> to match parts of tags, for example:<br>"
            "&nbsp;&nbsp;&nbsp;<b>abc*</b> or <b>*free</b> both match <b>ABC1free</b><br>"
            "&nbsp;&nbsp;&nbsp;<b>*</b> matches all site content<br>"
            "{{help_license_tags}}"
            .format( intro ) )


class ContentTagMatchMixin( models.Model ):
    """
    To increase flexibility and avoid DB links to content, the ties to content
    is through CASE-INSENSITIVE matching on license tags (with '*' wildcard).
    This allows product defined that are cross-cutting to content relationships.

    The relationship between a content's tags and tag matches may be:
        1-way - Coupons and APAs see if they match content
        2-way - PAs see if they match content, Items see if they match PAs
    """

    # Link to content license tags via pattern matching
    # Entered/stored as a comma-delimited list that is parsed when needed
    _tag_matches = models.CharField( blank=True, max_length=mc.CHAR_LEN_UI_LONG,
                verbose_name=u"License tags", db_column='tag_matches' )

    class Meta:
        abstract = True

    @property
    def tag_matches( self ):
        """
        Override to support combining/override tag_matches from different source
        """
        return self._tag_matches

    @property
    def includes_all( self ):
        return '*' in self.tags

    @property
    def tags( self ):
        """
        Parse tags string into tuple of cleaned short names
        """
        return comma_tuple( self.tag_matches )

    @stash_method_rv
    def matches_tag( self, content_tag ):
        """
        Does this object's tags match a content item/collection.
        Blank item_tags are only matched by products that include all.
        """
        rv = self.includes_all
        if not rv and content_tag:
            rv = tag_match( content_tag, self.tags )
        log.detail3("Matches tag: %s, %s -> %s", self, content_tag, rv)
        return rv

    @stash_method_rv
    def content_dict( self, *args, **kwargs ):
        """
        Provides completely loaded content dict with trees and item info.
        BIG DB HIT, use appropriately.
        """
        log.debug("Getting product content dict: %s", self)
        base_items = self.get_content( BaseItem.objects.filter, *args, **kwargs )
        return content_dict( base_items )

    @stash_method_rv
    def get_top_collections( self ):
        """
        Returns list of top collections associated with this object.
        """
        log.debug("Getting product top collections: %s", self)
        return self.get_content( Tree.objects.filter_tops )

    def get_content( self, filter_fn, *args, **kwargs ):
        """
        Uses DB matching to return list of content items that match our tags,
        given a filter_fn that returns a content queryset.
        If there is DB error due to tag or regex formation, return null set.
        """
        kwargs.update({ 'sandbox': self.sandbox, 'workflow__in': 'PBDQ' })
        try:
            if not self.includes_all:
                args += ( tags_Q( self.tags ) ,)

            return list( set( filter_fn( *args, **kwargs ) ) )

        except Exception as e:
            log.info("CONFIG - Bad content filter: %s -> %s: %s, %s",
                        e, self, args, kwargs)
            if settings.DEBUG and not settings.MP_TESTING:
                raise
        return self.__class__.objects.none()

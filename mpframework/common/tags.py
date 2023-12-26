#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logic for matching text tags with each other.
    MPF uses as the basis to configure flexible connections
    between systems entities, like content and licenses.

    This logic is duplicated here for Python and DB matching, and
    DUPLICATED IN CLIENT CODE for optimizing comparisons there.

    Regular expression matching is supported, but since the logic
    needs to be supported for DB searches, the scope of regex
    will be limited to the DB support.
"""
import re
from django.db.models import Q
from django.core.validators import RegexValidator
from django.conf import settings

from . import log


# Django validator for content item tags
validate_item_tag = RegexValidator( re.compile( r'^[-\.\w]+\Z', re.U ),
    u"Please use only use letters, numbers, or _-.", 'invalid' )

NEGATION_DELIM = '!'
REGEX_DELIM = '/'


def tag_match( tag, tag_matches ):
    """
    Determine if a given tag matches tag_matches (case insensitive).
    DOES NOT include check for includes all, as that is managed
    separately by the APA.
    """
    rv = False
    tag = str( tag ).strip()
    if tag:
        tag = tag.lower()
        # Exact match
        rv = tag in tag_matches
        # Otherwise check case and wildcard matching
        if not rv:
            for tm in tag_matches:
                rv = _tag_match( tm, tag )
                if rv:
                    break
    return rv

def _tag_match( match_tag, item_tag ):
    # EXACT MATCH ALREADY HANDLED

    # Setup for one return with negation
    rv = False
    negative = False
    if match_tag.startswith( NEGATION_DELIM ):
        negative = True
        match_tag = match_tag.strip( NEGATION_DELIM )

    # Regular expression match
    if match_tag.startswith( REGEX_DELIM ):
        try:
            match_tag = match_tag.strip( REGEX_DELIM )
            match_re = re.compile( match_tag, re.IGNORECASE )
            rv = match_re.match( item_tag )
        except Exception as e:
            log.info("CONFIG - Bad regex tag match: %s -> %s", match_tag, e)
            if settings.MP_DEV_EXCEPTION:
                raise

    if not rv:
        # Embedded wildcard by checking for fragments between
        # wildcards in the order they are presented by removing
        # each match as it occurs
        match_text = match_tag.strip('*')
        frags = match_text.split('*')
        if len( frags ) > 1:
            rv = True
            for frag in frags:
                if frag in item_tag:
                    item_tag = item_tag.replace( frag, '', 1 )
                else:
                    rv = False
                    break
        # Check wildcards on the ends
        elif match_tag.startswith('*') and match_tag.endswith('*'):
            rv = match_text in item_tag
        elif match_tag.startswith('*'):
            rv = item_tag.endswith( match_text )
        elif match_tag.endswith('*'):
            rv = item_tag.startswith( match_text )

    return bool(rv) ^ negative


def tags_Q( tags, tag_field='tag' ):
    """
    Return Q for whether any tag match expressions in tags match
    any content tags in a query filter.
    """
    q = Q()
    for tag in tags:
        q |= tag_Q( tag, tag_field )
    return q

def tag_Q( tag, tag_field='tag' ):
    """
    Implement same logic as wildcards in tag_match, by building up
    Q queries for filter args.
    """
    q = Q()

    # Setup for negation
    negative = False
    if tag.startswith( NEGATION_DELIM ):
        negative = True
        tag = tag.strip( NEGATION_DELIM )

    # Handle regular expression
    if tag.startswith( REGEX_DELIM ):
        tag = tag.strip( REGEX_DELIM )
        q = Q(**{ tag_field + '__iregex': tag })

    if not q:
        tag_text = tag.strip('*')

        # Add cases for matches in middle
        frags = tag_text.split('*')
        if len( frags ) > 1:
            # HACK - don't try to replicate the order of fragments
            for frag in frags:
                filt = { tag_field + '__icontains': frag }
                q &= Q( **filt )

        # Handle other cases
        if not q:
            if tag.startswith('*') and tag.endswith('*'):
                filt = '__icontains'
            elif tag.startswith('*'):
                filt = '__iendswith'
            elif tag.endswith('*'):
                filt = '__istartswith'
            else:
                filt = '__iexact'
            q = Q(**{ tag_field + filt: tag_text })

    return ~q if negative else q

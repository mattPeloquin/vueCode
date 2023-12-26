#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF base template
"""
import re
from django.template import Template
from django.template import Context
from django.template.context import make_context

from .. import log


class mpTemplate( Template ):
    """
    Provide a wrapper to:

        - Make a Django base Template look like a new "backend template"
        - Make Django template object picklable for caching
        - Support any option processing

    The mpTemplate assumes it will be handed text for the template, so all
    determining of how to load the template code is already done.
    """

    def __init__( self, template_code, option=None ):
        assert isinstance( template_code, str )
        self.option = option
        super().__init__( template_code )

    def __str__( self ):
        return str( getattr( self, 'name', self.source[:80] ) )

    def render( self, context=None, request=None ):
        """
        Django's addition of swappable templates in 1.10 changed
        the Template object used by TemplateResponse.
        Calling context here without worrying about the backend works as
        MPF assumes only one template backend engine is used.
        """
        log.detail3("Rendering template: %s", self)
        if not isinstance( context, Context ):
            context = make_context( context, request )
        code = super().render( context )

        # Apply any option processing to the final output to make sure
        # any embedded templates are captured
        if self.option:
            code = self.apply_option( code )

        return code

    def __getstate__( self ):
        """
        Rebuild template from source to avoid trying to pickle template node
        objects. This saves a DB hit for custom templates, but still has
        expensive template rendering, so cache as much rendered HTML as possible.
        """
        log.detail3("Pickling template: %s", self)
        state = [ self.source, self.option ]
        return state
    def __setstate__( self, state ):
        self.__init__( state[0], state[1] )

    def apply_option( self, code ):
        """
        Provide text inside or outside tags to support blending
        CSS/JS content and link/script tags in the same template,
        whose parts can be loaded separated by MPF.
        """
        part = _template_parts.get( self.option )
        if part:
            code = part.findall( code )
            code = '\n'.join( code )
        return code

_template_parts = {
    'CSS_LINKS_ONLY': re.compile(
        r'<link \b .*? >', re.DOTALL | re.VERBOSE ),
    'SCRIPT_LINKS_ONLY': re.compile(
        r'<script \b .*? src .*? ></script>', re.DOTALL | re.VERBOSE ),
    'CSS_CONTENT_ONLY': re.compile(
        r'<style>(.*?)</style>', re.DOTALL | re.VERBOSE ),
    'SCRIPT_ONLY': re.compile(
        r'<script .*? (?!\b src\=) .*? </script>', re.DOTALL | re.VERBOSE ),
    }

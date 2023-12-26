#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Extends Django 'include' to check for MPF custom templates

    Unlike include, cannot be handed a template directly, only
    a path to template file, or name of custom template.

    Implements 'with' option to add context...
        ...BUT NOT 'only' for isolating context
"""
from django.conf import settings
from django.template import Library
from django.template.base import token_kwargs
from django.template.base import Node

from mpframework.common import log


# Load the template tag into Django custom tag registry
register = Library()


class mpTemplateFindNodeMixin:

    def mp_handle_options( self, kwargs ):
        """
        template_type allows selecting only from the given type
        template_option supporting spliting links from content
        """
        self.extra_context = kwargs.pop( 'extra_context', {} )
        self.template_option = str(self.extra_context.pop( 'template_option', '' ))
        self.template_type = str(self.extra_context.pop( 'template_type', '' ))

    def mp_get_template( self, context ):
        sandbox = context['site']
        user = context['user']
        assert sandbox and user

        # Resolve name with context in case it has replacement
        template_name = self.template_name.resolve( context )

        # Load template via Sandbox
        return sandbox.get_template( template_name, use_dev=user.workflow_dev,
                    option=self.template_option,
                    template_type=self.template_type )


class mpTemplateIncludeNode( Node, mpTemplateFindNodeMixin ):
    """
    Adapt Django IncludeNode to render templates using named custom templates
    and workflow modification of templates. Expects one of:
        - Name for MPF CustomTemplate
        - CustomTemplate object
        - Path to template
    """

    def __init__( self, name, **kwargs ):
        self.template_name = name
        self.mp_handle_options( kwargs )

    def render( self, context ):
        """
        Load and reneder the template.
        Inclusion nodes are not used in loops, so don't do any caching in context.
        """
        try:
            template = self.mp_get_template( context )
            if template:
                # Add context for the 'with' option
                values = { name: var.resolve( context ) for name, var
                            in self.extra_context.items() }
                with context.push( **values ):

                    return template.render( context )

        except Exception as e:
            log.exception("mp_include: %s -> %s", self.template_name, e)
            if settings.MP_TEMPLATE_DEBUG or settings.MP_TESTING:
                raise
        return ''

@register.tag
def mp_include( parser, token ):
    """
    MPF template include that checks for sandbox overrides
    """
    bits = token.split_contents()
    name = parser.compile_filter( bits[1] )

    # Only support with option with limited error handling for now
    options = {}
    remaining_bits = bits[2:]
    while remaining_bits:
        option = remaining_bits.pop( 0 )
        if option == 'with':
            value = token_kwargs( remaining_bits, parser, support_legacy=False )
        options[ option ] = value

    return mpTemplateIncludeNode( name,
                extra_context=options.get( 'with', {} ).copy(),
                )

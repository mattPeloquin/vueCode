#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Like Django extends, but for mpTemplates in DB
"""
from django.conf import settings
from django.template import Library
from django.template.base import token_kwargs
from django.template.loader_tags import BlockNode
from django.template.loader_tags import ExtendsNode

from mpframework.common import log

from .mp_include import mpTemplateFindNodeMixin


# Load the template tag into Django custom tag registry
register = Library()

class mpTemplateExtendsNode( ExtendsNode, mpTemplateFindNodeMixin ):

    def __init__( self, nodelist, parent_name ):
        """
        Setup values needed by ExtendsNode
        """
        self.template_name = parent_name
        self.nodelist = nodelist
        self.blocks = { n.name: n for n in
                nodelist.get_nodes_by_type( BlockNode )
                }
        self.mp_handle_options( {} )

    def get_parent( self, context ):
        return self.mp_get_template( context )

@register.tag
def mp_extends( parser, token ):
    """
    Unlike Django extends, mp_extends will not work recursively
    """
    bits = token.split_contents()
    parent_name = parser.compile_filter( bits[1] )
    nodelist = parser.parse()
    return mpTemplateExtendsNode( nodelist, parent_name )

#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Theme Code shared with Sandbox and Frame

    Themes are a set of templates and options used to load a sandbox
    (or specific request to a sandbox with request skin options).
    Some elements set defaults that can be overridden by collections, others
    are defined by request, frame, and/or sandbox.

    Some theme elements are single selection:

        - Viewer, Login, Panel

    Others are added into the CSS space, providing a framework-specific way
    to break down CSS into mix-and-match chunks. Obviously this is by
    convention, as there is nothing to prevent CSS from being added wherever
    to override the intent of a theme. In order of precedence:

        Style - Defines borders, shadows, relative sizes, animation. Can define
                global colors (shadows) or use theme color classes define in Color.
        Mixin - Additional style snippets.
        Font - Should only contain font types, not sizes
        Color - Should only have color and global (white) sheen definitions;
                normally color should NOT deal with shadows, frames, etc. as those
                are handled in styles
"""
from django.db import models

from mpframework.common import constants as mc
from mpframework.common.model.fields import YamlField
from mpframework.common.model.fields import mpImageField

from .template import TemplateCustom


class ThemeMixin( models.Model ):
    """
    Themes are determined by selection of custom templates for mixing in
    specific code - these are defaulted in the sandbox and overridden in frames
    """

    # Portal layout templates
    _default_panel = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='default_panel_id',
                related_name='+', blank=True, null=True )
    _default_nav = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='default_nav_id',
                related_name='+', blank=True, null=True )
    _default_node = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='default_node_id',
                related_name='+', blank=True, null=True )
    _default_item = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='default_item_id',
                related_name='+', blank=True, null=True )
    _default_viewer = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='default_viewer_id',
                related_name='+', blank=True, null=True )

    # Other structural templates
    _login = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='login_id', related_name='+', blank=True, null=True )

    # Styling
    _style = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='style_id', related_name='+', blank=True, null=True )
    _font = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='font_id', related_name='+', blank=True, null=True )
    _color = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='color_id', related_name='+', blank=True, null=True )
    _color2 = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='color2_id', related_name='+', blank=True, null=True )
    _mixin = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='mixin_id', related_name='+', blank=True, null=True )
    _mixin2 = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='mixin2_id', related_name='+', blank=True, null=True )
    _mixin3 = models.ForeignKey( TemplateCustom, models.SET_NULL,
                db_column='mixin3_id', related_name='+', blank=True, null=True )

    # Default background, used if no page-specific background provided
    _background_image = mpImageField(
                db_column='background_image', blank=True, null=True )

    # CSS dropped on every page at the end of of the <style> block loading
    css_head = models.TextField( max_length=mc.TEXT_LEN_MED, blank=True )

    # Sitebuilder configurable sandbox options
    sb_options = YamlField( null=True, blank=True )

    class Meta:
        abstract = True

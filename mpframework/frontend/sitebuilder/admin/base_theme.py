#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared theme admin code
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models import Frame
from ..models import TemplateCustom
from .content_mixin import ContentOptionMixin


class ThemeFormBase( BaseModelForm, ContentOptionMixin ):
    """
    Assumes model inheritance from ThemeMixin AND FrameSelectMixin
    """
    class Meta:
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'frame_site': "Site VuePortal",
            'frame_tree': "Collection VuePortal",
            'frame_item': "Item VuePortal",
            '_default_panel': "Page layout",
            '_default_nav': "Nav display",
            '_default_node': "Node display",
            '_default_item': "Item display",
            '_default_viewer': "Viewer",
            '_login': "Login",
            '_style': "Portal style",
            '_mixin': "Mixin style 1",
            '_mixin2': "Mixin style 2",
            '_mixin3': "Mixin style 3",
            '_color': "Default color",
            '_color2': "Alternate color",
            '_font': "Font",
            '_background_image': "Default background",
            'css_head': "Custom CSS added to pages",
            'sb_options': "SiteBuilder options",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'frame_site': "Select the site's portal layout<br>"
                    "(create custom VuePortals with SiteBuilder).",
            'frame_tree': "Layout used with with collection portals, which "
                    "are URLs that show only 1 collection.",
            'frame_item': "Layout used with item portals, which are URLs "
                    "that show only 1 item.",
            '_login': "Select the layout for sign-in and sign-up.",
            '_default_panel': "Default collection page layout template "
                    "(may be overridden)",
            '_default_nav': "Default navigation element display template "
                    "(may be overridden)",
            '_default_node': "Default child collection node layout template "
                    "(may be overridden)",
            '_default_item': "Default content item display template "
                    "(may be overridden)",
            '_default_viewer': "Default content viewer layout template "
                    "(may be overridden)",
            '_style': "The primary UI style used with all portals.<br>"
                    "(create custom styles with SiteBuilder)",
            '_mixin': "Mixins modify the main style.",
            '_mixin2': "Mixins modify the main style.",
            '_mixin3': "Mixins modify the main style.",
            '_color': "Select the default color palette.<br>"
                    "(create custom palettes with SiteBuilder)",
            '_color2': "Select alternate colors a user can choose.<br>"
                    "(e.g., for a dark or light mode)",
            '_font': "Select font group.<br>"
                    "(create custom font groups with SiteBuilder)",
            '_background_image': "Use this image as background on any pages "
                    "that do not define their own background image.<br>"
                    "The image is faded by default, which can be adjusted with CSS.<br>"
                    "Leave blank for no background image (i.e., use theme colors).",
            'css_head': "This CSS code is loaded in head <style></style> tags for "
                    "all site pages.<br>"
                    "Look for EasyStyle es_ prefixed classes.<br>"
                    "{help_easy_style}",
            'sb_options': "Customize names, behavior, layout, etc.<br>"
                    "{help_sb_options}",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'css_head': CodeEditor( mode='css', rows=24 ),
            'sb_options': CodeEditor( mode='yaml', theme='default', rows=16 ),
            })

    site__background_image_opacity = forms.CharField( required=False,
            label="Background image opacity",
            help_text="Adjust the opacity of the background image." )
    site__theme_padding = forms.CharField( required=False,
            label="Default theme padding",
            help_text="Change the default padding used around the edges "
                "of panels." )
    site__user_bar_height = forms.CharField( required=False,
            label="User bar height",
            help_text="Change the height of the top user bar." )
    site__user_bar_padding = forms.CharField( required=False,
            label="User bar padding",
            help_text="Change the padding around the top user bar." )
    breakpoints__width_small = forms.CharField( required=False,
            label="Responsive width small breakpoint",
            help_text="Set pixel width where small transitions to medium." )
    breakpoints__width_medium = forms.CharField( required=False,
            label="Responsive width medium breakpoint",
            help_text="Set pixel width where medium transitions to large." )
    breakpoints__width_large = forms.CharField( required=False,
            label="Responsive width large breakpoint",
            help_text="Set pixel width where large transitions to extra large." )
    breakpoints__height_small = forms.CharField( required=False,
            label="Responsive height small breakpoint",
            help_text="Set pixel height where small transitions to medium." )
    breakpoints__height_medium = forms.CharField( required=False,
            label="Responsive height medium breakpoint",
            help_text="Set pixel height where medium transitions to large." )

    yaml_form_fields = BaseModelForm.yaml_form_fields.copy()
    yaml_form_fields.update({
        'sb_options': {
            'form_fields': [
                'breakpoints__width_small', 'breakpoints__width_medium',
                'breakpoints__width_large',
                'breakpoints__height_small', 'breakpoints__height_medium',
                ] + ContentOptionMixin.yaml_form_fields_extensions,
        }})

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        # Fixup fields
        for field in ThemeAdminBase._fields:
            theme_field = self.fields.get( field )
            if theme_field:
                theme_field.empty_label = u"Use default"


class ThemeAdminBase( BaseTenantAdmin ):

    def __init__( self, *args, **kwargs ):

        # HACK - Support read only filed lookups for system yaml fields
        for name, field in ContentOptionMixin.base_fields.items():
            def yaml_field( obj ):
                dot_name = name.replace( '__', '.' )
                return obj.sb_options.get( dot_name, '' )
            yaml_field.short_description = name
            setattr( self, name, yaml_field )

        super().__init__( *args, **kwargs )

    def access_Q( request ):
        return TemplateCustom.has_access_Q( request.user.staff_level )

    _fields = {
        'frame_site': ( Frame.objects, 'PROVIDER_OPTIONAL', ('frame_type','P') ),
        'frame_tree': ( Frame.objects, 'PROVIDER_OPTIONAL', ('frame_type','C') ),
        'frame_item': ( Frame.objects, 'PROVIDER_OPTIONAL', ('frame_type','I') ),
        '_login': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','L'), ('Q',access_Q) ),
        '_default_panel': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','Q'), ('Q',access_Q) ),
        '_default_nav': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','N'), ('Q',access_Q) ),
        '_default_node': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','R'), ('Q',access_Q) ),
        '_default_item': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','I'), ('Q',access_Q) ),
        '_default_viewer': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','F'), ('Q',access_Q) ),
        '_font': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','A'), ('Q',access_Q) ),
        '_style': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','B'), ('Q',access_Q) ),
        '_color': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','C'), ('Q',access_Q) ),
        '_color2': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','C'), ('Q',access_Q) ),
        '_mixin': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','D'), ('Q',access_Q) ),
        '_mixin2': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','D'), ('Q',access_Q) ),
        '_mixin3': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                    ('template_type','D'), ('Q',access_Q) ),
        }
    filter_fk = dict( BaseTenantAdmin.filter_fk, **_fields )

    changed_fields_to_save = ( 'sb_options', 'css_head' )

    fieldset_theme_style = [
        ('_style','portal__hero_style'),
        ('_font','_color'),
        ('_color2','_mixin'),
        ('_mixin2','_mixin3'),
        ('_background_image','site__background_image_opacity'),
        ]

    fieldset_theme_layout = [
        ('_default_panel','_default_node'),
        ('_default_item','_default_nav'),
        ('_login','_default_viewer'),
        ]

    fieldset_theme_options = ContentOptionMixin.fieldset_item + \
        ContentOptionMixin.fieldset_collection + [
        ('site__user_bar_height','site__user_bar_padding'),
        ('breakpoints__width_small','breakpoints__width_medium'),
        'breakpoints__width_large',
        ('breakpoints__height_small','breakpoints__height_medium'),
        ]

    readonly_fields_system = list( _fields ) + [
        'css_head', 'sb_options', '_background_image',
        ] + ContentOptionMixin.yaml_form_fields_extensions

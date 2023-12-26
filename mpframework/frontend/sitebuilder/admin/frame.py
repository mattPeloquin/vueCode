#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Frame admin
"""
from django import forms

from mpframework.common import _
from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.ops.admin import FieldChangeMixin
from mpframework.foundation.tenant.admin import ProviderOptionalAdminMixin

from ..models import Frame
from ..models import TemplateCustom
from .base_theme import ThemeAdminBase
from .base_theme import ThemeFormBase


# HACK - Translate from frame type to allowed pane type
FRAME_PANE_TYPE = {
    'P': 'P',   # Portal
    'C': 'G',   # Collection
    'I': 'H',   # Item
    }


class FrameForm( ThemeFormBase ):
    class Meta:
        model = Frame
        exclude = ()
        labels = dict( ThemeFormBase.Meta.labels, **{
            'frame_type': "VuePortal Type",
            '_script_name': "Script name",
            'simple_pane': "Simple pane",
            })
        help_texts = dict( ThemeFormBase.Meta.help_texts, **{
            'name': "Name used to refer to the VuePortal in the admin UI",
            'frame_type': "Select whether this portal is intended for site, collection "
                    "or individual item usage",
            '_script_name': "Name used in system options and URLs.<br>"
                    "Leave blank to use name.",
            'simple_pane': "Select a single pane for the VuePortal with default options, "
                    "or define one or more panes in the structure.",
            })
        widgets = dict( ThemeFormBase.Meta.widgets, **{
            'name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_CODE ),
            'structure': CodeEditor( mode='yaml', theme='default', rows=24 ),
            })

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        if self.fields.get('simple_pane'):
            self.fields['simple_pane'].empty_label = u"Use structure below"


class FrameAdmin( FieldChangeMixin, ProviderOptionalAdminMixin,
                ThemeAdminBase ):
    form = FrameForm

    list_display = ( 'provider_item', 'name', 'frame_type',
            'staff_level', 'notes' )
    list_display_links = ( 'name' ,)
    search_fields = ( 'name', '_script_name', 'notes' )
    ordering = ( '-provider_optional', 'frame_type', 'name' )

    # Define explicit read-only fields for system items to prevent CodeMirror
    # fields from being turned into read-only text fields
    readonly_fields_system = [ 'frame_type', 'structure', 'simple_pane',
            'name', '_script_name', 'notes',
            ] + ThemeAdminBase.readonly_fields_system

    changed_fields_to_save = ( 'structure' ,)

    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': (
                ('name','_script_name'),
                ('frame_type','notes'),
                'simple_pane',
                'structure',
                'css_head',
                )
            }),
        (_("Theme overrides"), {
            'mp_staff_level': 'access_all',
            'classes': ('mp_collapse',),
            'fields': ThemeAdminBase.fieldset_theme_layout + \
                ThemeAdminBase.fieldset_theme_style + \
                ThemeAdminBase.fieldset_theme_options + \
                ['sb_options']
            }),
        ("ROOT", {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'provider_optional',
                'staff_level',
                )
            }),
        ]

    def get_object( self, request, *args ):
        obj = super().get_object( request, *args )
        # Need to update filter_fk to use the right pane type
        self.filter_fk.update({
            'simple_pane': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                        ( 'template_type', FRAME_PANE_TYPE[ obj.frame_type ] ) ),
            })
        return obj

    @property
    def can_copy( self ):
        return True

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        if self.type_filter:
            qs = qs.filter( frame_type__in=self.type_filter )
        return qs


class FrameStaffAdmin( StaffAdminMixin, FrameAdmin ):
    type_filter = 'PCI'

staff_admin.register( Frame, FrameStaffAdmin )

class FrameRootAdmin( FrameAdmin ):
    type_filter = None
    list_editable = ( 'frame_type', 'staff_level', 'notes' )

root_admin.register( Frame, FrameRootAdmin )

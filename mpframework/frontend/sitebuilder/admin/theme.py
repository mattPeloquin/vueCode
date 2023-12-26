#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Theme admin
"""
from django import forms

from mpframework.common import _
from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.foundation.ops.admin import FieldChangeMixin
from mpframework.foundation.tenant.admin import ProviderOptionalAdminMixin

from ..models import Theme
from .base_theme import ThemeAdminBase
from .base_theme import ThemeFormBase


class ThemeForm( ThemeFormBase ):
    class Meta:
        model = Theme
        exclude = ()
        labels = dict( ThemeFormBase.Meta.labels, **{
            })
        help_texts = dict( ThemeFormBase.Meta.help_texts, **{
            'name': _("Name used to refer to the theme in the admin UI"),
            })
        widgets = dict( ThemeFormBase.Meta.widgets, **{
            'name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_CODE ),
            })

class ThemeAdmin( FieldChangeMixin, ProviderOptionalAdminMixin, ThemeAdminBase ):
    form = ThemeForm
    list_display = ( 'provider_item', 'name', 'staff_level', 'notes' )
    list_display_links = ( 'name' ,)
    list_text_small = ThemeAdminBase.list_text_small + (
            'staff_level', )
    search_fields = ( 'name', 'css_head' )
    ordering = ( 'provider_optional', 'name' )

    # Define explicit read-only fields for system items
    readonly_fields_system = ThemeAdminBase.readonly_fields_system + [
            'name', 'notes' ]

    changed_fields_to_save = ThemeAdminBase.changed_fields_to_save

    fieldsets = [
        ("", {
            'classes': ('mp_collapse',),
            'fields': (
                ('name','notes'),
                )
            }),
        (_("Layout"), {
            'mp_staff_level': 'access_med',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                'frame_site',
                ] + ThemeAdminBase.fieldset_theme_layout,
            }),
        (_("Styling"), {
            'mp_staff_level': 'access_low',
            'classes': ('mp_collapse',),
            'fields': ThemeAdminBase.fieldset_theme_style,
            }),
        (_("Options"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse',),
            'fields': [
                ('frame_tree','frame_item'),
                ] + ThemeAdminBase.fieldset_theme_options + [
                'css_head',
                ]
            }),
        (_("Advanced options"), {
            'mp_staff_level': 'access_all',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'sb_options',
                )
            }),
        ( "ROOT", {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'staff_level',
                'provider_optional',
                )
            }),
        ]

    @property
    def can_copy( self ):
        return True

#--------------------------------------------------------------------

class ThemeStaffAdmin( StaffAdminMixin, ThemeAdmin ):
    helptext_changelist = _("Themes bring together style and layout to "
        "create unique user experiences")

staff_admin.register( Theme, ThemeStaffAdmin )

class ThemeRootAdmin( ThemeAdmin ):
    list_editable = ( 'staff_level', 'notes' )
root_admin.register( Theme, ThemeRootAdmin )

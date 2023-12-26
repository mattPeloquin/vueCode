#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal groups admin
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import HtmlEditor
from mpframework.foundation.tenant.admin import ProviderOptionalAdminMixin
from mpframework.frontend.sitebuilder.models import TemplateCustom
from mpframework.content.mpcontent.tags import tag_code_help

from ..models import PortalGroup
from .base_visibility import BaseVisibilityForm
from .base_visibility import BaseVisibilityAdmin


class PortalGroupForm( BaseVisibilityForm ):
    class Meta:
        model = PortalGroup
        exclude = ()

        labels = dict( BaseVisibilityForm.Meta.labels, **{
            'scope': "Use with",
            '_script_name': "Script name",
            'nav_template': "Nav display",
            'item_template': "Item display",
            'text1': "Footer description",
            'html': "HTML header",
            })
        labels_sb = dict( BaseVisibilityForm.Meta.labels_sb, **{
            'html': "html",
            })
        help_texts = dict( BaseVisibilityForm.Meta.help_texts, **{
            'scope': "Optionally limit group to collections or items.",
            '_script_name': "Name used in templates.",
            '_tag_matches': tag_code_help(),
            'nav_template': "Display navigation elements "
                    "(usually collections) using this template.",
            'item_template': "Display content items with this template.",
            'html': "HTML displayed above the group.",
            'text1': "Optional text to display below the group.",
            })
        widgets = dict( BaseVisibilityForm.Meta.widgets, **{
            '_tag_matches': forms.Textarea( attrs=mc.UI_TEXTAREA_DEFAULT ),
            'html': HtmlEditor( rows=8 ),
            })

    portal__show_empty = forms.BooleanField( required=False,
            label="Show group when empty",
            help_text="Select this to always show group, even if it contains "
                "no content." )

    yaml_form_fields = BaseVisibilityForm.yaml_form_fields.copy()
    yaml_form_fields['sb_options']['form_fields'].extend([
            'portal__show_empty',
            ])

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        if self.fields.get('nav_template'):
            self.fields['nav_template'].empty_label = u"Use default"
        if self.fields.get('item_template'):
            self.fields['item_template'].empty_label = u"Use default"


class PortalGroupAdmin( ProviderOptionalAdminMixin, BaseVisibilityAdmin ):
    form = PortalGroupForm

    list_display = ( 'provider_item', '_name', '_tag_matches', 'scope',
            '_script_name', 'description', 'hist_modified', 'hist_created'
            )
    list_editable = BaseVisibilityAdmin.list_editable + (
            'scope', '_tag_matches', '_script_name' )
    ordering = ( '-provider_optional', '_name' )

    search_fields = ( '_name', '_tag_matches' )

    filter_fk = dict( BaseVisibilityAdmin.filter_fk, **{
        'item_template': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                            ('template_type','I') ),
        'nav_template': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                            ('template_type','N') ),
        })

    changed_fields_to_save = BaseVisibilityAdmin.changed_fields_to_save + (
            'html',)

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.ld_insert_pos = 3

    @property
    def can_copy( self ):
        return True

    def get_fieldsets( self, request, obj=None ):
        """
        Adjust fields based on user privilege
        """
        rv = super().get_fieldsets( request, obj )
        user = request.user
        top = rv[ self.fs_top ][1]['fields']
        custom = rv[ self.fs_custom ][1]['fields']

        # Remove items user shouldn't see for system
        if obj and obj.is_system:
            del top[1]

        # Groups display is different from most content
        del top[1]  # remove text1, image1
        top.insert( 1, ( 'scope','_script_name') )
        top.insert( 2, ('html',) )
        top.insert( 3, ('item_template', 'nav_template') )
        top.insert( 4, ('_tag_matches', 'portal__show_empty') )
        top.insert( 5, ('notes') )
        custom.insert( 0, ('text1', 'image1') )
        if user.access_root:
            top.insert( 0, ('provider_optional',) )
        return rv

    def description( self, obj ):
        if obj.provider_optional is None:
            return obj.notes
        else:
            return "{}, {}".format( obj.get_workflow_display(),
                                    self.active_sandboxes( obj ) )
    description.short_description = "Description"

root_admin.register( PortalGroup, PortalGroupAdmin )


class PortalGroupStaffAdmin( StaffAdminMixin, PortalGroupAdmin ):
    pass

staff_admin.register( PortalGroup, PortalGroupStaffAdmin )

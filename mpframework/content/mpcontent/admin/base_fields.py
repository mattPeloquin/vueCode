#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content admin shared across all content and with
    content-like display items such as badges.
"""
from django import forms

from mpframework.common import _
from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.form import mpHtmlFieldFormMixin
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.ops.admin import FieldChangeMixin

from ..models import BaseContentFields


class BaseFieldForm( mpHtmlFieldFormMixin, BaseModelForm ):
    sanitize_html_fields = ( 'text1', 'text2' )
    class Meta:
        model = BaseContentFields
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            '_name': "Name",
            'image1': "Main image",
            'image2': "Small image or icon",
            'text1': "Main description",
            'text2': "Additional text",
            'sb_options': "SiteBuilder Options",
            })
        labels_sb = dict( BaseModelForm.Meta.labels_sb, **{
            '_name': "name",
            'image1': "image1",
            'image2': "image2",
            'text1': "text1",
            'text2': "text2",
            'sb_options': "options",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            '_name': "Name of this content item.<br>"
                    "The name is shown in all page layouts and reporting.",
            'text1': "Optional content description shown in the portal.<br>"
                    "How this text displays depends on page layout.",
            'text2': "Optional additional text. Where this text appears "
                    "depends on the page layout.",
            'image1': "Optional image for the content.<br>"
                    "Location depends on page layout.",
            'image2': "Optional image for use in smaller displays.<br>"
                    "Location depends on page layout.",
            'sb_options': "YAML data sent to the client as JSON.<br>"
                    "Used for SiteBuilder options and sending custom data.<br>"
                    "{help_sb_options}",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            '_name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_LARGE ),
            'text1': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            'text2': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            'sb_options': CodeEditor( mode='yaml', theme='default', rows=24 ),
            })

class BaseFieldAdmin( FieldChangeMixin, BaseTenantAdmin ):
    """
    Shared behavior for admin of BaseAttr types
    Most functionality defined here is shared between Attrs and Items,
    while some is used by Attrs admin directly, and other parts are
    overridden in the BaseItem admin. Goals is to minimize overall code.

    NOTE - one assumption is that users with basic access would never
    have access to an Attr admin screen, so no need to hide items
    only visible in basic here.
    """
    form = BaseFieldForm

    # HACK - provide client JS value to use for public media
    media_client_url = 'mpurl.content_media_url'

    list_display = ( '_name', 'hist_modified', 'hist_modified' )
    list_display_links = ( '_name' ,)
    list_col_large = BaseTenantAdmin.list_col_large + (
        '_name', )

    list_filter = ( 'hist_modified', 'hist_created' )
    search_fields = ( '_name' ,)

    changed_fields_to_save = ( '_name', 'text1', 'text2' )

    # Fieldset group numbers used to dynamically setup fields
    # Improves readability of custom inserts and fieldset reorder
    fs_top = 0
    fs_content = 0
    fs_custom = 1
    fs_advanced = 2

    # Fieldset is a list instead of tuple to allow manipulation
    # Fields that need to be manipulated based on staff access are in lists vs. tuples
    fieldsets = [
        ("", {
            'fields': [
                ('_name',),
                ('text1','image1'),
                ]
            }),
        (_("Additional text and images"), {
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ('text2','image2'),
                ]
            }),
        (_("Advanced"), {
            'mp_staff_level': 'access_all',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                'sb_options',
                ('hist_modified','hist_created'),
                ]
            }),
        ("ROOT", {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                'revision',
                ]
            }),
        ]

    def __init__( self, *args, **kwargs ):
        """
        Setup field insert pos
        """
        super().__init__( *args, **kwargs )
        self.ld_insert_pos = 1

    def change_view( self, request, object_id, form_url='', extra_context=None ):
        response = super().change_view(
                    request, object_id, form_url, extra_context )
        # Support pop-up editing screens returning
        if request.GET.get('return_to'):
            redirect = str( request.GET.get('return_to') )
            log.debug("Redirecting to: %s", redirect)
            response['location'] = redirect
        return response

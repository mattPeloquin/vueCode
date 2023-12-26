#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Embed HTML page admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import CodeEditor

from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import Embed


class EmbedForm( BaseItemForm ):
    class Meta:
        model = Embed
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'head': "Head content",
            'body': "Body content",
            'add_style': "Add site style",
            'head_template': "Head as template",
            'body_template': "Body as template",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'head': "Scripting or CSS loaded in the page head.",
            'body': "HTML, scripting, etc. loaded in the page body.<br>"
                    "This can include snippets for embedding web forms, videos "
                    " or other services, raw HTML from editors, etc.",
            'add_style': "Add site styling to the embed iframe",
            'head_template': "Process the head content as a {{ root_name }} template. "
                    "Unselect if there is a scripting conflict.",
            'body_template': "Process the body content as a {{ root_name }} template. "
                    "Select to use {{ root_name }} server scripting in the body.",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            'head': CodeEditor( mode='css', rows=12 ),
            'body': CodeEditor( mode='css', rows=28 ),
            })


class EmbedAdmin( BaseItemAdmin ):
    form = EmbedForm

    changed_fields_to_save = BaseItemAdmin.changed_fields_to_save + (
                                'head', 'body' )

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user

        new_rows = [ 'body' ]
        if user.access_high:
            new_rows = [
                'add_style',
                'body',
                'body_template',
                'head',
                'head_template',
                ]

        rv[ self.fs_content ][1]['fields'][0:0] = new_rows
        return rv

root_admin.register( Embed, EmbedAdmin )


class EmbedStaffAdmin( StaffAdminMixin, EmbedAdmin ):
    pass

staff_admin.register( Embed, EmbedStaffAdmin )


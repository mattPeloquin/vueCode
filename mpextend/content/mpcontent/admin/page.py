#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    ProtectedPage admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import HtmlEditor
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import ProtectedPage


class ProtectedPageForm( BaseItemForm ):
    class Meta:
        model = ProtectedPage
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'html': "Page HTML",
            'allow_print': "User can print page contents",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            'allow_print': "allow_print",
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'html': "Enter the HTML content that will be protected here; this must be purchased to be seen",
            'allow_print': "Enable to allow users to print this page contents.",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            'html': HtmlEditor( rows=32, protected=True ),
            })


class ProtectedPageAdmin( BaseItemAdmin ):

    form = ProtectedPageForm

    changed_fields_to_save = BaseItemAdmin.changed_fields_to_save + ( 'html' ,)

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user

        new_rows = [ ('html',) ]
        rv[ self.fs_content ][1]['fields'][0:0] = new_rows

        return rv

root_admin.register( ProtectedPage, ProtectedPageAdmin )


class ProtectedPageStaffAdmin( StaffAdminMixin, ProtectedPageAdmin ):
    pass

staff_admin.register( ProtectedPage, ProtectedPageStaffAdmin )


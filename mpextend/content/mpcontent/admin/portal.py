#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Portal item admin screens
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import HtmlEditor
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import PortalItem


class PortalItemForm( BaseItemForm ):
    class Meta:
        model = PortalItem
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            })


class PortalItemAdmin( BaseItemAdmin ):
    form = PortalItemForm

    def get_fieldsets( self, request, obj=None ):
        """
        PortalItems don't have protected content
        """
        rv = super().get_fieldsets( request, obj )

        # Replace protected content area with HTML
        rv.pop( self.fs_html )
        rv.pop( self.fs_content )
        rv.insert( self.fs_content,
            ("Public content", {
                'classes': ('mp_collapse',),
                'fields': (
                    'html1',
                    'html2',
                    )
                }),
            )

        # Remove items from base that aren't used
        # HACK - the field tuples must be kept in sync with BaseItemAdmin
        if request.user.access_high:
            rv[ self.fs_options ][1]['fields'].remove(
                    ('portal__coming_soon','portal__no_trials') )
            rv[ self.fs_options ][1]['fields'].remove(
                    ('access__free_user','access__free_public') )

        return rv

root_admin.register( PortalItem, PortalItemAdmin )


class PortalItemStaffAdmin( StaffAdminMixin, PortalItemAdmin ):
    pass

staff_admin.register(PortalItem, PortalItemStaffAdmin )

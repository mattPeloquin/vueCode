#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin screens for content related models
"""
from copy import deepcopy
from django import forms

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ...lms.views.admin_new import lms_add_subview
from ...lms.views.admin_update import lms_update_subview
from ..models import LmsItem


class LmsItemForm( BaseItemForm ):
    class Meta:
        model = LmsItem
        exclude = ()
        labels = dict( BaseItemForm.Meta.labels, **{
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            })

    # HACK - place package puttons under action
    _action = forms.ChoiceField( choices=LmsItem.ACTION_TYPICAL, required=False,
                help_text="""
    Select how this content is delivered to users<br>
    User experience may vary based on their browser settings.<br>

    <div class="mp_flex_line">
        <input id="package_update" class="mp_button" value="Update Package File" />
        <input id="package_metrics" class="mp_button" value="Show Package Metrics" />
        <input id="package_force" class="mp_button" value="Force Latest Package" />
        </div>

    <div id="package_update_dialog" class="mp_template">
        <h3>Update LMS Package</h3>
        <form id="package_update_form" class="mp_form" method="post"
                enctype="multipart/form-data"
                >
            {% include "_/form.html" with form=package_update_form %}

            <input type="submit" class="mp_button" name="upload_package"
                    value="Update package" />

            </form>
        </div>

    <div id="package_dialog" class="mp_template">
        <div id="package_display"></div>
        </div>
    """ )


class LmsItemStaffAdmin( StaffAdminMixin, BaseItemAdmin ):
    form = LmsItemForm

    def changelist_view( self, request, extra_context=None ):
        """
        Add support for mini new LMS package form
        """
        extra_context = extra_context or {}
        extra_context['lms_add_form'] = lms_add_subview( request )
        return super().changelist_view( request, extra_context )

    def change_view( self, request, object_id, form_url='', extra_context=None ):
        """
        Add context support for package form
        """
        update_form = lms_update_subview( request )
        extra_context = extra_context or {}
        extra_context['package_update_form'] = update_form
        return super().change_view( request, object_id,
                                                     form_url, extra_context=extra_context )

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user
        return rv

staff_admin.register( LmsItem, LmsItemStaffAdmin )


class LmsItemAddStaffAdmin( LmsItemStaffAdmin ):

    def changelist_view( self, request, extra_context=None ):
        """
        Add context to direct template to click the add button
        """
        extra_context = extra_context or {}
        return super().changelist_view( request, extra_context )

class LmsItemAddAdminProxy( LmsItem ):
    class Meta:
        app_label = 'mpcontent'
        proxy = True

staff_admin.register( LmsItemAddAdminProxy, LmsItemAddStaffAdmin )


class LmsItemRootAdmin( BaseItemAdmin ):
    form = LmsItemForm

    list_display = BaseItemAdmin.LIST_START + (
            'package_root' ,) + BaseItemAdmin.LIST_END

    list_filter = BaseItemAdmin.list_filter + ( 'package_root' ,)

    search_fields = BaseItemAdmin.search_fields + ( '=package_root__id',
            'package_root__current__archive_name',
            '=package_root__current__id' )

    fieldsets = deepcopy( BaseItemAdmin.fieldsets )
    fieldsets[ BaseItemAdmin.fs_content ][1]['fields'] += ('package_root',)

root_admin.register( LmsItem, LmsItemRootAdmin )

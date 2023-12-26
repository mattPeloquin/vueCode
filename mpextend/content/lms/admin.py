#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    LMS Package admin
"""
from django import forms
from django.db.models import Count

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import mpListFilter
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.tenant.admin import TabularInlineView

from .models import Package
from .models import PackageRoot


class PackageUserCountAdminMixin:
    """
    Behavior shared between package screen and inline, including
    adding metrics about user connections to packages
    """

    def get_queryset( self, request ):
        provider = request.user.provider
        qs = super().get_queryset( request )
        return qs.filter( _provider=provider )

    def user_count( self, obj ):
        return obj.user_count
    user_count.short_description = 'User connections'
    user_count.admin_order_field = 'user_count'

#------------------------------------------------------------------------

class PackageForm( BaseModelForm ):
    class Meta:
        model = Package
        exclude = ()

        widgets = dict( BaseModelForm.Meta.widgets, **{
            'run_name': forms.TextInput( attrs={'size': 120} ),
            'archive_name': forms.TextInput( attrs={'size': 120} ),
            'launch_file': forms.TextInput( attrs={'size': 60} ),
            })

RootFilter = mpListFilter.new( PackageRoot, 'Root', 'package_root_id' )

class PackageAdmin( PackageUserCountAdminMixin, BaseTenantAdmin ):
    form = PackageForm

    list_display = ( '__str__', 'user_count', 'run_ready', 'mounting', 'package_type', 'lms_type',
                        'launch_file', 'hist_modified', 'package_root' )
    list_editable = ( 'run_ready', 'mounting', 'package_type', 'lms_type', 'launch_file' )

    list_filter = ( RootFilter, 'package_type', 'lms_type', 'launch_file', 'run_ready',
                    'hist_modified', 'hist_created')

    search_fields = ( '=package_root__id', 'archive_name', 'run_name' )

    fieldsets = [
        ("Summary", {
            'classes': ('mp_collapse',),
            'fields': (
                ('run_ready', 'mounting'),
                'launch_file',
                'run_name',
                'archive_name',
                ('package_type', 'lms_type'),
                'package_root',
                '_provider',
                ('hist_created', 'hist_modified'),
                )
            }),
        ]

root_admin.register( Package, PackageAdmin )

#------------------------------------------------------------------------

class PackageRootForm( BaseModelForm ):
    class Meta:
        model = PackageRoot
        exclude = ()

        widgets = {
            }

class PackageInline( PackageUserCountAdminMixin, TabularInlineView ):
    model = Package
    fields = ('run_ready', '__str__', 'user_count')
    readonly_fields = fields

class PackageRootAdmin( BaseTenantAdmin ):
    form = PackageRootForm
    inlines = ( PackageInline, )

    list_display = ( '__str__', 'current', 'package_count', 'item_count',
                     'hist_modified' )
    list_filter = ( 'packages', 'hist_modified', 'hist_created')

    search_fields = ( '=current__id', 'current__archive_name',
                      'current__run_name')

    fieldsets = [
        ("Summary", {
            'classes': ('mp_collapse',),
            'fields': (
                '_provider',
                'current',
                ('hist_created', 'hist_modified'),
                )
            }),
        ("Packages", {
            'classes': ('mp_placeholder packages-group',),
            'fields' : (),
            }),
        ]


    def get_queryset( self, request ):
        qs = super().get_queryset( request )

        # Add metrics about user connections to packages
        qs = qs.annotate(
                _item_count = Count( 'lms_items', distinct=True ),
                _package_count = Count( 'packages', distinct=True ),
                )

        return qs

    def package_count( self, obj ):
        return obj._package_count
    package_count.short_description = 'Packages'
    package_count.admin_order_field = '_package_count'

    def item_count( self, obj ):
        return obj._item_count
    item_count.short_description = 'LmsItems'
    item_count.admin_order_field = '_item_count'


root_admin.register( PackageRoot, PackageRootAdmin )


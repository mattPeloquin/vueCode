#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base mixin for MPF Admin classes
"""
from django.contrib.admin.helpers import flatten_fieldsets

from .. import log
from ..view import staff_required
from .base_changelist import BaseChangeList


class AdminSharedMixin:
    """
    Functionality shared in Admin pages and Inlines
    """
    list_field_css = {}
    after_create_fieldsets = None
    list_add_root = ('id',)

    # Set default ordering for admin changelists and lookup filters
    ordering = ('-id',)

    # Responsive support, assuming size breakpoints and css names
    list_hide_med = ()
    list_hide_small = ('id',)
    list_text_small = ()
    list_text_xsmall = ()
    list_col_small = ('id',)
    list_col_med = ()
    list_col_large = ()
    list_col_xlarge = ()

    def get_changelist( self, request, **kwargs ):
        return BaseChangeList

    def get_list_hide_med( self, request ):
        return self.list_hide_med
    def get_list_hide_small( self, request ):
        return self.list_hide_small + self.list_hide_med
    def get_list_text_small( self, request ):
        return self.list_text_small
    def get_list_text_xsmall( self, request ):
        return self.list_text_xsmall
    def get_list_col_small( self, request ):
        return self.list_col_small
    def get_list_col_med( self, request ):
        return self.list_col_med
    def get_list_col_large( self, request ):
        return self.list_col_large
    def get_list_col_xlarge( self, request ):
        return self.list_col_xlarge

    # HACK - stash object as early as possible
    def get_object( self, request, *args ):
        obj = super().get_object( request, *args )
        request.mpstash['admin_obj'] = obj
        return obj

    def fieldset_id( self, fieldsets, name ):
        """
        Given fieldsets, return index of name; to support dynamic
        manipulation of fieldsets based on user access
        """
        index = 0
        for fs in fieldsets:
            if fs[0] and str(fs[0]).startswith( name ):
                return index
            index += 1

    def get_field_queryset( self, _db, db_field, request ):
        """
        Force use of default DB to get values for admin.
        """
        return super().get_field_queryset( 'default', db_field, request )

    @property
    def all_fields( self ):
        """
        Cached flat list of all fields that will be displayed
        """
        rv = getattr( self, '_all_fields', None )
        if not rv:
            if self.fieldsets:
                rv = flatten_fieldsets( self.fieldsets )
            else:
                rv = self.field_names
            self._all_fields = rv
        return rv

    def get_list_display( self, request ):
        """
        Add root info to list display for root users
        """
        rv = super().get_list_display( request )
        rv = list( rv )
        if request.user.access_root:
            rv.extend([ name for name in self.list_add_root if name not in rv  ])
        return rv

    def get_list_display_links( self, request, list_display ):
        """
        Add id to editing on root screen for convenience
        """
        rv = super().get_list_display_links( request, list_display )
        if request.user.access_root:
            rv = list( rv )
            rv.append('id')
        return rv

    # Provide injectable context to admin form rendering

    @staff_required
    def render_change_form( self, request, context, **kwargs ):
        """
        This is best place to add extra content for changes, because it happens
        after the object has been retrieved in changeform_view
        """
        context = ( context and context.copy() ) or {}
        self.add_context( context, request, kwargs.get('add') )

        # Pass along admin copy requests to template
        if self.can_copy and request.GET.get('mpf_admin_copy_request'):
            context['admin_copy_request'] = True
        if request.GET.get('mpf_admin_copy_save'):
            context['admin_copy_save'] = True
        if request.GET.get('mpf_admin_copy_new'):
            context['admin_copy_new'] = True

        rv = super().render_change_form( request, context, **kwargs )
        log.timing("FINISH ADMIN changeform: %s", request.mptiming)
        return rv

    @staff_required
    def changelist_view( self, request, extra_context=None ):
        """
        Add MPF context to changelist
        """
        log.timing("START ADMIN render: %s", request.mptiming)
        rv = super().changelist_view( request,
                    extra_context=self.add_context( extra_context, request ) )
        log.timing("FINISH ADMIN changelist: %s", request.mptiming)
        return rv

    @staff_required
    def delete_view( self, request, object_id, extra_context=None ):
        rv = super().delete_view( request, object_id,
                    extra_context=self.add_context( extra_context, request ) )
        return rv
    @staff_required
    def history_view( self, request, object_id, extra_context=None ):
        return super().history_view( request, object_id,
                    extra_context=self.add_context( extra_context, request ) )

    def add_context( self, context, request, add=False ):
        """
        Context processing shared across view types, modifies existing
        or creates new context and returns it.
        """
        context = context or {}
        context.update({
            'is_view_only': self.is_view_only( request ),
            'has_add_permission': self.has_add_permission( request ),
            'can_delete': self.can_delete,
            'can_copy': self.can_copy and not add,
            'can_ajax_save': self.can_ajax_save and not add,

            'helptext_changelist': self.helptext_changelist,
            'helptext_changeform': self.helptext_changeform,
            'helptext_changeform_add': self.helptext_changeform_add,

            # HACK - JS location for an admin's change page's public media
            'media_client_url': getattr( self, 'media_client_url', 'mpurl.media_url' ),
            })
        return context

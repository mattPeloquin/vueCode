#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF Admin base for both MPF an non-MPF models
"""
from django.conf import settings
from nested_admin import NestedModelAdmin

from .. import log
from ..form import BaseModelForm
from ..model.related import add_related_fields
from .base_mixin import AdminSharedMixin


class BaseAdmin( AdminSharedMixin, NestedModelAdmin ):
    """
    Base class all MPF admin pages, including pages for Django models
    """

    # MPF admin makes some assumptions about what form can handle
    form = BaseModelForm

    # Turn off automatic list select related, since MPF objects should
    # explicitly designate their select relation relationships
    list_select_related = False

    # Assume the root admin pages are used unless overridden by staff
    # pages - do not use this for access rights
    root_page = True

    # This can be tuned for specific screens
    list_per_page = settings.MP_ADMIN['LIST_PAGINATION']

    # Help text
    helptext_changelist = ''
    helptext_changeform = ''
    helptext_changeform_add = ''

    def get_form( self, request, obj=None, **kwargs ):
        """
        Override admin form class to provide user and sandbox context
        """
        OldForm = super().get_form( request, obj, **kwargs )
        class NewForm( OldForm ):
            def __new__( cls, *args, **kwargs ):
                kwargs['mpf_request'] = request
                return OldForm( *args, **kwargs )

        return NewForm

    def get_queryset( self, request ):
        """
        Add model's select and prefetch fields to the default changelist queryset
        """
        qs = super().get_queryset( request )

        # Add related fields from model declarations
        qs = add_related_fields( qs, self.model, group='admin' )

        # Force use of master DB to avoid issues with read replica lag
        qs = qs.using('default')

        # HACK - Fix for the "fix" in Django #11313 that caused ALL rows for a model
        # to be loaded when a changelist view is saved. Originally overloaded all of
        # changelist_view, but now use subset approach from #28238 for cleaner integration
        if 'POST' == request.method:
            ids = self._get_changelist_post_ids( request )
            if ids:
                qs = qs.filter( id__in=ids )

        log.timing2("ADMIN queryset: %s", request.mptiming)
        return qs

    def _get_changelist_post_ids( self, request ):
        # HACK - provide the IDs involved in the current post
        rv = []
        field_num = 0
        while True:
            id = request.POST.get( 'form-{}-id'.format( field_num ) )
            if id:
                rv.append( id )
            else:
                break
            field_num += 1
        return rv

    def get_changelist_instance( self, request ):
        """
        Support dynamic get_list_editable settings.
        """
        self.list_editable = self.get_list_editable( request )
        return super().get_changelist_instance( request )

    # Support MPF customization of list display

    def list_insert( self, current, insert, offset=0, list_insert_pos='ld_insert_pos' ):
        """
        Support inserting into lists (list_display) with values that may
        be inherited across classes
        """
        pos = getattr( self, list_insert_pos, 0 ) + offset
        # Adjust for any programatically added list_action
        if 'list_actions' in current:
            pos += 1
        rv = current[:pos] + insert + current[pos:]
        return rv

    def get_list_display( self, request ):
        rv = super().get_list_display( request )
        if self.can_copy or self.can_delete:
            rv = ['list_actions'] + list( rv )
        return rv

    def get_list_display_links( self, request, list_display ):
        # Grab second item in list display links if defaulted to first
        rv = super().get_list_display_links( request, list_display )
        # Adjust for any programatically added list_action
        if 'list_actions' in rv:
            rv = list( list_display )[1:2]
        return rv

    def get_list_editable( self, request ):
        return self.list_editable

    # Checks that can be overridden

    def is_view_only( self, request ):
        return False

    @property
    def can_copy( self ):
        return False

    @property
    def can_ajax_save( self ):
        return True

    @property
    def can_delete( self ):
        return False

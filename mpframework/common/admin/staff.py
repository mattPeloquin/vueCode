#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for Django staff admin screens
"""
from django.http import Http404

from .. import log


class StaffAdminMixin:
    """
    Add functionality for ALL provider/staff screens that use Django admin

    This should be used with ALL admin screens attached to staff_admin

    ASSUMES TenantAdminMixin and ModelAdmin ARE INHERITED AFTER,
    this mixin needs to go first in class definitions to ensure its
    calls are first, so it can override any other base class routines

    Non-provider staff should not see most sandbox information, ala flatland.
    Tenant-related fields are hidden based on provider status, even though in
    most cases the staff admin config wouldn't ask for those fields.

    Root-only items are removed from the site object at startup, while
    the provider items are removed on a per-request basis.
    """

    # Use the staff admin for these pages
    root_page = False

    # Fields that are always hidden to provider staff
    _ROOT_ONLY_FIELDS = ( 'id', '_provider', 'provider_optional' )

    # Fields with these names will be hidden if user isn't a provider
    _SEES_SANDBOXES_FIELDS = ( 'sandbox' ,)

    _MEMBERS_TO_CHECK_FOR_FIELD_HIDING = [
            'fields', 'search_fields',
            'list_display', 'list_display_links',
            'list_filter', 'list_editable',
            ]

    # Override in admin classes to limit access
    see_changelist = True

    def save_form( self, request, form, change ):
        obj = super().save_form( request, form, change )
        return obj

    def save_model( self, request, obj, form, change ):
        """
        Add tenancy information to new objects
        Provider is never seen on staff screens, and depending on screen and
        privileges, sandbox relationships also won't be set on the form when creating.
        For the root console, all tenancy fields are visible and changed manually.
        """
        user = request.user
        if not change and not user.logged_into_root:
            sandbox = request.sandbox

            # Always force setting required tennacy fields, even if they are
            # not present -- because Django will throw an exception at this
            # point because the FK relationship doesn't exist, can't test for
            # existence with hasattr, and doesn't hurt to set if not relevant
            obj.sandbox = sandbox
            obj._provider = sandbox.provider

            # Only set optional provider if present, as the attr is checked for,
            # and since it allows NULL, hasattr works
            if hasattr( obj, 'provider_optional' ):
                obj.provider_optional = sandbox.provider

        super().save_model( request, obj, form, change )

    def has_delete_permission( self, request, obj=None ):
        """
        Do not allow deletions through provider staff screens
        """
        return False

    #-----------------------------------------------------------------
    # Modify admin layout based on context

    def __init__( self, *args, **kwargs ):
        """
        Use initialization to disable root admin functionality providers don't see
        This is done at startup since it applies to all provider admin screens
        """
        super().__init__( *args, **kwargs )

        # Hide the actions dialog; don't want to support deletes here
        self.actions = None

        # Also remove root fields from all other display class members
        for member in self._MEMBERS_TO_CHECK_FOR_FIELD_HIDING:
            fields = getattr( self, member )
            if fields:
                log.detail3("Hiding root fields from: %s", member)
                fields = [ f for f in fields if not
                            any( str( f ) == name for name in self._ROOT_ONLY_FIELDS )
                            ]
                setattr( self, member, tuple( fields ) )

    """--------------------------------------------------------------------
        Dynamically adjust fields for staff UI based on user privilege

        Changes made here are only applied to staff admin screens.
        Adjustments made to both Staff and Sandbox Root screens should
        be done in TenantAdminMixin
    """

    def changelist_view( self, request, extra_context=None ):
        if not self.see_changelist:
            raise Http404
        return super().changelist_view( request, extra_context )

    def get_list_display( self, request ):
        rv = super().get_list_display( request )
        rv = self._adjust_fields( request.user, rv )
        return rv

    def get_fieldsets( self, request, obj=None ):
        """
        Filter per-request fieldsets based on user privilege
        """
        user = request.user
        rv = super().get_fieldsets( request, obj )

        if not user.sees_sandboxes:
            log.detail3("Removing provider fields from fieldsets: %s -> %s", user, self)
            self._adjust_fieldsets( self._SEES_SANDBOXES_FIELDS, rv )

        return rv

    def _adjust_fields( self, user, fields ):
        """
        Per-request hiding of fields in a flat list based in user privilege
        """
        rv = fields
        if not user.sees_sandboxes:
            log.detail3("Hiding provider fields: %s", fields)
            rv = [ f for f in fields if f not in self._SEES_SANDBOXES_FIELDS ]
        return rv

    def _adjust_fieldsets( self, fields_to_hide, fieldsets, prefix_to_hide=None ):
        """
        Modify given fieldset in place to provide deeper exclude based
        on name prefix and specific fields.
        This can be used to modify both class and per-request
        """
        for fieldset in fieldsets:

            # Remove entire fieldset based on naming convention
            if prefix_to_hide:
                if str( fieldset[0] ).startswith( prefix_to_hide ):
                    log.detail3("Removing fieldset due to name: %s", fieldset[0])
                    fieldsets.remove( fieldset )
                    continue

            # Hide fields (THIS WILL HIDE GROUPS IF ONLY ONE MATCHES)
            # Support one level of tuple nesting to get names
            # by converting to sets and testing for overlap
            # (if no tuple string will be mangled into set, but should be harmless)
            if fieldset[1]:
                log.detail3("Removing fieldset fields: %s => %s", fieldset[0], fields_to_hide)

                fieldset[1]['fields'] = [ f for f in fieldset[1]['fields'] if
                                            ( f not in fields_to_hide and
                                              set( f ).isdisjoint( set( fields_to_hide ) ))
                                            ]


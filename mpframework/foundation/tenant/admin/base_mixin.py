#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared admin code for MPF tenant filtering of Django Admin
"""

from mpframework.common import log
from mpframework.common.admin.filter import mpListFilter

from ..query_filter import tenant_filter_form_fk
from ..models.sandbox import Sandbox
from ..models.base import TenantManager


class TenantAdminMixin:
    """
    Filters Admin model views to show only items a user can see
    Is the basis for staff admin screens, providing multitenancy.

    ASSUMES ModelAdmin IS INHERITED AFTER
    ASSUMES model has default manager that uses TenantQuerySet

    Whether sandbox or provider scope is shown in admin depends on the
    tenant_filter processing.
    """

    # HACK FUTURE- this exists because common base admin depends on some behavior
    # from this mixin that is incompatible if the model does not use
    # TenantQuerySet - if classes are reworked to remove dependency or if
    # all models use TenantQuerySet, remove this
    no_tenant_filter = False

    # Override this in classes where the changelist and items outside
    # the sandbox should only be seen by users with sees_sandboxes privilege
    sees_sandboxes_required = False

    def get_queryset( self, request ):
        """
        Filter admin items according to tenant

        Adds the request to queryset tenant filtering, to provide filtering by
        the kwargs filtering in tenant_filter
        """
        qs = super().get_queryset( request )
        kwargs = {}
        if not self.no_tenant_filter:
            kwargs.update({
                'request': request,
                'admin_filter': True,
                })
        qs = qs.filter( **kwargs )
        return qs

    def add_context( self, context, request, add=False ):
        """
        Add tenancy context
        """
        context = super().add_context( context, request, add )
        context.update({
            # Note whether the staff screen requires sees_sandboxes privilege
            # Doesn't provide tenant security; used to redirect
            'sees_sandboxes_required': self.sees_sandboxes_required,
            })
        return context

    """--------------------------------------------------------------------
        Filter FK and MTM field choices to provider or sandbox

        The filter_fk and filter_mtm dicts can be added to in derived classes
        for each FK or MTM field to filter in admin based on their relationships
    """
    filter_fk = {}
    filter_mtm = {}

    def formfield_for_foreignkey( self, db_field, request, **kwargs ):
        """
        Make foreign key choices only contain items for this provider
        """
        _fixup_admin_filter_kwargs( self, 'filter_fk', db_field, request, kwargs )
        return super().formfield_for_foreignkey( db_field, request, **kwargs )

    def formfield_for_manytomany( self, db_field, request, **kwargs ):
        """
        Cut down the choices in MTM select items to show only items from the
        provider or sandbox related to the admin item
        """
        _fixup_admin_filter_kwargs( self, 'filter_mtm', db_field, request, kwargs )
        return super().formfield_for_manytomany( db_field, request, **kwargs )

    """--------------------------------------------------------------------
        Adjust fields based on Tenancy and Root site
    """

    def get_list_display( self, request ):
        rv = super().get_list_display( request )
        return self._add_root_fields( request.user, rv )

    def get_list_filter( self, request ):
        rv = super().get_list_filter( request )
        rv = self._convert_filters( rv )
        return rv

    def get_search_fields( self, request ):
        """
        Add ID to all Django admin searching
        """
        rv = super().get_search_fields( request )
        rv = list( rv )
        if 'id' not in rv:
            rv += ['=id']
        return rv

    def _add_root_fields( self, user, name_list ):
        """
        Add display and filter names for root site
        """
        if user.logged_into_root:
            if 'sandbox' in self.field_names and 'sandbox' not in name_list:
                name_list.insert( 0, 'sandbox' )
            if '_provider' in self.field_names and '_provider' not in name_list:
                name_list.insert( 0, '_provider' )
            elif 'provider_optional' in self.field_names:
                name_list.insert( 0, 'provider_optional' )
        return name_list

    def _convert_filters( self, filter_list ):
        """
        Support automatic conversion of sandbox list filters
        """
        def convert( filter ):
            if filter == 'sandbox' or filter == '_sandbox':
                return mpListFilter.new( Sandbox, u"Site", 'sandbox_id' )
            else:
                return filter

        return [ convert( filter ) for filter in filter_list ]


def _fixup_admin_filter_kwargs( admin_model, field_filters, db_field, request,
                kwargs_to_update ):
    """
    Provides setup of the kwargs queryset filtering in django admin
    fields using declarative data in the admin models.
    Can be used for both screen fields and inlines
    """

    # See if there is a filter relationships specified in admin class
    filter_config = getattr( admin_model, field_filters, None )
    if not filter_config:
        log.debug_on() and log.detail3("Admin had no filters: %s -> %s",
                                   admin_model.__class__.__name__, db_field.name )
        return
    filters = list( filter_config.get( db_field.name, () ) )
    if not filters:
        log.debug_on() and log.debug("UNFILTERED ADMIN: %s -> %s",
                                   admin_model.__class__.__name__, db_field.name )
        return

    sandbox = request.sandbox
    provider = sandbox.provider

    # HACK - ROOT SANDBOX is special -- It allows visibility into everything in
    # changelists, but for field relationships tie to provider for items
    if request.user.logged_into_root:

        # If change screen where there is a specific object, filter on tenancy
        if getattr( admin_model, 'obj', None ):
            sandbox = getattr( admin_model.obj, 'sandbox', None )
            if sandbox:
                provider = sandbox.provider
            else:
                provider = getattr( admin_model.obj, '_provider', None )
            log.info2("Root sandbox admin filter spoofing: %s -> %s, %s",
                        admin_model.obj, sandbox, provider )
        else:
            # FUTURE - if there are many values that could be displayed in the
            # UI consider removing from UI or locking access or adding select
            # provider setting to root admin
            sandbox = None
            provider = None
            log.info("ROOT SANDBOX field filter with no object")

    log.debug_on() and log.detail3("Filtering admin field: %s, %s, %s -> %s, %s",
                            admin_model.__class__.__name__, provider, sandbox,
                            db_field.model.__name__, db_field.name )

    # Use passed in queryset or start with manager (all objects)
    manager = filters.pop( 0 )
    qs = kwargs_to_update.get( 'queryset', manager )

    # Setup queryset filtering based on well known names
    fk_type = filters.pop( 0 )

    # Add any additional filters
    filter_kwargs = { name: value for name, value in filters }

    # Fixup any dynamic Qs
    Qarg = filter_kwargs.get('Q')
    if Qarg and callable( Qarg ):
        filter_kwargs['Q'] = Qarg( request )

    # Apply admin model ordering if none provided
    if not 'ORDERING' in filter_kwargs:
        related_admin = admin_model.admin_site._registry.get(
                db_field.remote_field.model )
        if related_admin is not None:
            filter_kwargs['ORDERING'] = related_admin.get_ordering( request )

    qs = tenant_filter_form_fk( sandbox, provider, qs, fk_type, **filter_kwargs )

    kwargs_to_update['queryset'] = qs

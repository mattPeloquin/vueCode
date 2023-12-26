#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared tenant filter logic used in multiple places
    to ensure scope is kept to sandbox or provider visibility
"""
from django.db.models import Q

from mpframework.common import log
from mpframework.common.utils import safe_int
from mpframework.common.model.utils import field_names


def tenant_filter_form_fk( sandbox, provider, qs, fk_type, **filter_kwargs ):
    """
    Returns a queryset for foreign key select boxes filtered for tenancy
    and optional additional filter kwargs.
    """

    # Well-known name filtering
    if fk_type == 'SANDBOX':
        filter_kwargs['sandbox'] = sandbox
    elif fk_type == 'PROVIDER':
        filter_kwargs['_provider'] = provider
    elif fk_type in [ 'PROVIDER_OPTIONAL', 'PROVIDER_OPTIONAL_REDUCE_NAME' ]:
        filter_kwargs['provider_optional_system'] = provider
    else:
        log.error("Bad Admin tenant relationship filter")

    # Q filtering
    Qarg = filter_kwargs.pop( 'Q', Q() )

    # Ordering
    ordering = filter_kwargs.pop( 'ORDERING', None )

    # Normally return lazy queryset for the select items
    qs = qs.mpusing('read_replica')\
            .filter( Qarg, **filter_kwargs )

    if ordering:
        qs = qs.order_by( *ordering )

    # Special case removing system items if custom item overrides
    # as no good way to exclude from DB filter.
    if fk_type == 'PROVIDER_OPTIONAL_REDUCE_NAME':
        qs = provider_optional_name_filter_fk( qs )

    return qs

def provider_optional_name_filter_fk( qs ):
    """
    Given a queryset for a provider optional select filter,
    remove any system items that have name duplicated.
    Need to get the data, and then do exclude on queryset so
    queryset can be returned.
    """
    custom_names = []
    system_names = []
    for item in list( qs ):
        ( system_names if item.is_system else custom_names )\
            .append( item.name )
    overrides = set(custom_names) & set(system_names)
    return qs.exclude(
            Q( provider_optional__isnull=True ) &
            Q( name__in=overrides ) )

#--------------------------------------------------------------------
# Tenant model relationships

def tenant_filter_parse( **kwargs ):
    """
    Fixup tenant filtering kwargs for use by tenant_filter_args
    """
    request = kwargs.pop( 'request', None )

    # Set the user if available
    user = request.user if request else kwargs.pop( 'user_filter', None )
    if user:
        kwargs['user_filter'] = user

    # Use the current logged in sandbox if only user provided
    sandbox = request.sandbox if request else kwargs.pop( 'sandbox', None )
    if user and not sandbox:
        sandbox = user.sandbox
        assert sandbox and user
    if sandbox:
        kwargs['sandbox'] = sandbox

    return kwargs

def tenant_filter_args( model, *args, **kwargs ):
    """
    Convert filtering args into specific DB filters related to tenancy
    """
    assert model

    # Convenience tenancy and security filter
    user = kwargs.pop( 'user_filter', None )

    # Separate admin from other requests
    admin = kwargs.pop( 'admin_filter', None )

    # These will be converted into more specific ID references
    provider = kwargs.pop( '_provider', None )
    sandbox = kwargs.pop( 'sandbox', None )
    provider_opt_sys = kwargs.pop( 'provider_optional_system', None )

    # Process any model or kwargs overrides for default filtering relationships
    # Always pop from kwargs, so won't be passed on as filter criteria
    tenant_arg_filter = kwargs.pop( 'tenant_arg_filter',
                            getattr( model, 'tenant_arg_filter',
                                _tenant_arg_filter ) )

    # Root sandbox has no tenant filtering restrictions
    if _root_sandbox( user, sandbox, provider ):
        log.debug("tenant_filter_args ROOT SANDBOX")
        return args, kwargs

    _args = []
    _kwargs = {}

    # Add system optional to provider_optional
    if not provider_opt_sys and (
            getattr( model, '_tenancy_type', None ) == 'provider_optional' ):
        provider_opt_sys = provider or ( sandbox and sandbox.provider )

    # Special support for getting both system and sandbox items
    if provider_opt_sys:
        _args.append( Q( provider_optional=provider_opt_sys ) |
                      Q( provider_optional__isnull=True ) )
    # Some models allow sees_sandboxes staff to to see provider scope WHEN...
    #   ...NOT filtered by user or sandbox limits
    #   ...NOT in a provider that is isolating sandboxes
    # For these cases, return all provider items (e.g., seeing all content
    # items can be assigned to different sandboxes)
    elif( admin and not sandbox and not provider and
            user and user.sees_sandboxes and
            getattr( model, 'provider_staff_sees_sandboxes', False ) ):
        log.db2("tenant provider filtering: %s", user)
        _args, _kwargs = tenant_arg_filter( model, None, user.provider )

    # If no filter criteria added yet, call sandbox filtering if possible
    if not ( _kwargs or _args ):
        if user and not ( sandbox or provider ):
            sandbox = user.sandbox
        _args, _kwargs = tenant_arg_filter( model, sandbox, provider )

    # Add new dict values and Q args
    kwargs.update( _kwargs )
    if _args:
        args += tuple( _args )

    # NOTE - experimented with flagging no tenant criteria here and in other
    # places in queryset processing. Problem is querysets are not called
    # immediately, and my be built up over time, in particular by Django admin
    # when processing Admin list filters. Thus flagging lack of tenancy args
    # here was not effective and special casing added complexity.
    log.debug_on() and log.db3("tenant filter DB args: %s -> %s, %s",
                                model, args, kwargs)

    return args, kwargs


def _tenant_arg_filter( model, sandbox, provider ):
    """
    Default tenant filtering (can be overridden by models)
    Return filter criteria for default sandbox, provider,
    and provider_optional relationships.
    HACK - the field names below are reserved words for field names
    """
    assert model
    fields = field_names( model )
    log.debug_on() and log.db3("Tenant filter: %s, %s => %s -> %s",
                sandbox, provider, model, fields)
    if sandbox:
        sandbox_id = safe_int( sandbox ) or sandbox.pk

        if 'sandbox' in fields:
            return (), { 'sandbox_id': sandbox_id }

        # Many to one link (as in content)
        if 'sandboxes' in fields:
            return (), { 'sandboxes': sandbox }
        if '_sandboxes' in fields:
            return (), { '_sandboxes': sandbox }

        # Handle sandbox staff and provider staff
        if 'user' in fields:
            return (), { 'user___provider__sandboxes': sandbox }

        if not provider:
            provider = getattr( sandbox, 'provider', None )

    if provider:
        provider_id = safe_int( provider ) or provider.pk

        # HACK - special case the provider filtering itself, e.g., in dumpscript
        if 'isolate_sandboxes' in fields:
            return (), { 'id': provider_id }

        # If provider relationship passed in, use it
        if '_provider' in fields:
            return (), { '_provider_id': provider_id }
        if 'provider_optional' in fields:
            return ( Q( provider_optional_id=provider_id ) |
                        Q( provider_optional__isnull=True ) ,), {}

        # Other direct relationships to provider; assumption is objects
        # with this relationships will always be within the provider
        if 'sandbox' in fields:
            return (), { 'sandbox___provider_id': provider_id }
        if 'user' in fields:
            return (), { 'user___provider_id': provider_id }

    return (), {}

def _root_sandbox( user, sandbox, provider ):
    try:
        if user and user.logged_into_root:
            return True
        if sandbox and sandbox.is_root:
            return True
        if provider and provider.is_root:
            return True
    except Exception:
        pass

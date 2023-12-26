#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Provider optional admin support
"""


class ProviderOptionalAdminMixin:
    """
    Supports use of provider optional items, which have both global
    versions and potentially provider-specific versions.
    """
    readonly_fields_system = ()

    def get_queryset( self, request ):
        """
        Can view root templates and templates assigned to this provider
        """
        return self.model.objects.filter( _provider=request.sandbox.provider )

    def get_readonly_fields( self, request, obj=None ):
        """
        By default, provider admin staff cannot modify system items.
        MPF displays such fields in special non-input tag on the admin page.
        Forms with fields like CodeEditor that don't display well as readonly
        need to define readonly_fields_system to exclude those fields
        """
        if( obj and obj.is_system
                and not request.GET.get('mpf_admin_copy_request')
                and not request.user.access_root ):

            # If explicit list provided
            if self.readonly_fields_system:
                return self.readonly_fields_system

            # Otherwise send all fields
            elif self.all_fields:
                return self.all_fields

        return self.readonly_fields

    def is_view_only( self, request ):
        obj = request.mpstash.get('admin_obj')
        return ( obj and obj.is_system ) and (
                   request.user and not request.user.access_root )

    def provider_item( self, obj ):
        return bool( obj.provider_optional )
    provider_item.short_description = "Custom"
    provider_item.order_field = 'provider_optional'
    provider_item.boolean = True

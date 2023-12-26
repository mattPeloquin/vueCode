#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    External lookup for model information

    Although the api is general and could provide information on any
    models, only models registered in Admin are supported.
"""
from django.conf import settings
from django.views.generic import View
from django.apps import apps

from mpframework.common import log
from mpframework.common.api import respond_api
from mpframework.common.view import staff_required


class Lookup( View ):
    """
    General model lookup for any model using TenantBaseManager
    """

    @staff_required
    def get( self, request, *args, **kwargs ):
        """
        Stash the sandbox for use in get_queryset and provide error quieting
        """
        try:
            self.GET = request.GET
            self.sandbox = request.sandbox
            self.model = apps.get_model( self.GET['app'], self.GET['model'] )

            data = self.get_data()
            if data:
                return respond_api( data )

        except Exception:
            # Log error noisily, but don't send error back to client
            log.exception("Problem with Autolookup: %s", self)
            if settings.MP_TESTING:
                raise
        return respond_api( self.error_data() )

    def get_data( self ):
        """
        Default data return is the json representation of model
        """
        limit = int( self.GET.get( 'limit', settings.MP_LOOKUP['LIMIT'] ) )
        return [ obj.json() for obj in
                    self.get_queryset()[ :limit ] ]

    def error_data( self ):
        """
        Default error placeholder
        """
        return {}

    def get_queryset( self ):
        """
        Default lookup uses the defined lookup queryset and search fields.
        """
        assert self.GET
        assert self.model
        assert self.sandbox
        log.debug2("Autolookup: %s -> %s", self, self.model)

        qs = self.model._default_manager.lookup_queryset( self.sandbox )
        if 'search' in self.GET:
            qs = qs.lookup_filter( self.GET['search'] )

        return qs.distinct()

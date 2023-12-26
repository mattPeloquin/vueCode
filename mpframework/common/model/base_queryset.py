#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared MPF functionality for querysets
"""
from django.db import models
from django.db.models import Q
from django.conf import settings


class BaseQuerySet( models.QuerySet ):

    def get_quiet( self, *args, **kwargs ):
        """
        Return none if doesn't exist, and ignores multiple
        """
        return self.filter( *args, **kwargs ).mpusing('read_replica').first()

    def mpusing( self, db_name ):
        """
        Support using read_replica with option to collapse to default DB
        for connection efficiency when there is no read replica configured.
        """
        if not settings.MP_DB_READ_REPLICA:
            db_name = 'default'
        return super().using( db_name )

    def lookup_filter( self, value, fields=None, order=None ):
        """
        Do case insensitive search for the value in search fields and id.
        """
        query = Q()
        fields = fields or getattr( self.model, 'lookup_fields', () )
        for field in fields:
            query |= Q(**{ field: value })
        qs = self.filter( query )

        order = order or getattr( self.model, 'lookup_order', () )
        if order:
            qs = qs.order_by( *order )

        return qs

    def lookup_from_list( self, obj_list, value ):
        """
        Replicate a lookup queryset from a list of objects.
        Supports simpler code when caching lists from previous searches.
        """
        def _lookup( obj ):
            try:
                if obj.pk == int(value):
                    return True
            except Exception:
                pass
            lookup_fields = getattr( self.model, 'lookup_fields', () )
            for field in lookup_fields:
                if getattr( obj, field ) == value:
                    return True
        return next( ( obj for obj in obj_list if _lookup( obj ) ), None )

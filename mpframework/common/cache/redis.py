#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django Redis cache extensions
"""
from django.utils.module_loading import import_string
from django_redis.cache import RedisCache
from django_redis.cache import omit_exception
from django_redis.client import DefaultClient


class mpRedisClient( DefaultClient ):
    pass


class mpRedisCache( RedisCache ):

    def __init__( self, server, params ):
        """
        Force use of MPF client
        """
        super().__init__( server, params )
        self._client_cls = import_string(
                'mpframework.common.cache.redis.mpRedisClient')

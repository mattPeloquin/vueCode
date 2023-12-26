#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Implement health check pings that include interaction with the DB
    and other servers.
"""
import os
import threading
from random import randint
from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.utils import IntegrityError

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.utils import timestamp
from mpframework.common.model import BaseModel
from mpframework.common.model.fields import YamlField


WORKER_NAME_LEN = 64


class HealthCheck( BaseModel ):
    """
    Each row represents FULL health check pings received by a
    particular server. These are stored primarily to exercise DB,
    but also provide some history.
    """
    server = models.CharField( unique=True, max_length=mc.CHAR_LEN_IP )
    checks = models.IntegerField( default=0 )
    history = YamlField( null=True, blank=True, safe_dict=False )

    @classmethod
    def ping( cls, ip ):
        ping = None
        try:
            ping = cls.objects.get( server=settings.MP_IP_PRIVATE )
        except cls.DoesNotExist:
            log.info2("New health check: %s", settings.MP_IP_PRIVATE)

        # Only save if ping is new or randomly
        if not ping or randint( 0, 1 ):
            try:
                with transaction.atomic():
                    if not ping:
                        ping = cls( server=settings.MP_IP_PRIVATE )
                    thread = threading.current_thread()
                    worker = '{} {}:{}'.format( settings.MP_PROFILE, os.getpid(), thread.name )
                    note = 'Check from: {} received by {}'.format( ip, worker )
                    ping.history[ timestamp() ] = note
                    ping.checks += 1
                    ping.save()
                    log.debug2("Saved health check: %s", note)
                    return "Performed DB read-write"

            except IntegrityError as e:
                log.info2("Health check collision: %s -> %s", ip, e)

        return "Performed DB read only"

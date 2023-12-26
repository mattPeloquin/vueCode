#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ops caching views
"""

from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.cache.clear import clear_cache
from mpframework.common.view import root_only

from mpframework.user.mpuser.models import mpUser


@root_only
def caching( request ):
    user = request.user
    if 'POST' == request.method:
        try:
            validated = request.POST.get('validate') == 'HELL YA'

            if 'reset_perf_all' in request.POST:
                log.info("CLEARING ALL PERFORMANCE CACHES -> %s", user)
                clear_cache('version')
                clear_cache('default')
                clear_cache('persist')
                clear_cache('template')
            if 'reset_perf_version' in request.POST:
                log.info("CLEARING VERSION CACHE -> %s", user)
                clear_cache('version')
            if 'reset_perf_default' in request.POST:
                log.info("CLEARING DEFAULT CACHE -> %s", user)
                clear_cache('default')
            if 'reset_perf_template' in request.POST:
                log.info("CLEARING TEMPLATE CACHE -> %s", user)
                clear_cache('template')

            if 'reset_sandbox' in request.POST:
                log.info("Invalidating sandbox: %s", request.sandbox)
                request.sandbox.invalidate()

            if 'reset_users' in request.POST:
                ids = request.POST.get( 'user_ids' ).split()
                log.info("Clearing user caching for: %s", ids)
                for id in ids:
                    mpUser.objects.get_from_id( request.sandbox, id ).invalidate()

            if validated and 'reset_sessions' in request.POST:
                log.info("RESETTING ALL USER SESSIONS! -> %s", user)
                clear_cache('users')

        except Exception:
            log.exception("Problem clearing caches from ops view")

    return TemplateResponse(request, 'root/ops/caching.html', {
                 })

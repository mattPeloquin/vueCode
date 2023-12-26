#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ops semi-automated cleanup views
"""

from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.view import root_only

from ...cleanups.utils import cleanup_shell


@root_only
def cleanups( request ):
    user = request.user

    # Text blobs that describe output of task
    output = []

    if 'POST' == request.method:
        commit = request.POST.get('validate') == 'HELL YA'
        limit = request.POST.get('limit')
        constraint = request.POST.get('constraint')
        try:

            if 'temp' in request.POST:
                from ...cleanups.one_off import one_off_cleanup
                output.extend( cleanup_shell( one_off_cleanup, user, commit, limit, constraint ) )

            if 'botstart' in request.POST:
                from ...cleanups.temp_bot import start_temp_bot
                output.extend( cleanup_shell( start_temp_bot, user, commit, limit, constraint ) )
            if 'botstop' in request.POST:
                from ...cleanups.temp_bot import stop_temp_bot
                stop_temp_bot()

            if 'tracking_clean_sessions' in request.POST:
                from mpframework.user.mpuser.tasks import tracking_clean_sessions
                output.extend( cleanup_shell( tracking_clean_sessions, user, commit, limit, constraint ) )

            if 'package_fixup' in request.POST:
                from mpextend.content.lms.tasks import package_fixup
                output.extend( cleanup_shell( package_fixup, user, commit, limit, constraint ) )
            if 'package_root_cleanup' in request.POST:
                from mpextend.content.lms.tasks import package_root_cleanup
                output.extend( cleanup_shell( package_root_cleanup, user, commit, limit, constraint ) )
            if 'package_leaf_cleanup' in request.POST:
                from mpextend.content.lms.tasks import package_leaf_cleanup
                output.extend( cleanup_shell( package_leaf_cleanup, user, commit, limit, constraint ) )
            if 'package_file_cleanup' in request.POST:
                from mpextend.content.lms.tasks import package_file_cleanup
                output.extend( cleanup_shell( package_file_cleanup, user, commit, limit, constraint ) )

        except Exception:
            log.exception("Problem with tasks view")

    request.method = 'GET'

    return TemplateResponse( request, 'root/ops/cleanups.html', {
                 'output': output,
                 })

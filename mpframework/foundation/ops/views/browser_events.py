#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Handle AJAX system events communicated by browser code
"""
from django.conf import settings
from django.core.cache import caches
from django.views.decorators.csrf import csrf_exempt

from mpframework.common import log
from mpframework.common.utils import now
from mpframework.common.utils import epoch_ms
from mpframework.common.api import respond_api_call


SANITY_SIZE = 8192


@csrf_exempt
def browser_message( request ):
    """
    Report loading errors on browser clients (when loading screen times out)
    """
    def handler( payload ):
        try:
            msg_type = payload['msg_type'].strip()
            info_tag = payload.get('request_tag')
            info = info_tag and caches['request'].get( info_tag )
            if info:
                now_ms = epoch_ms()
                total_ms = (now_ms - info['start_ms']) / 1000.0
                browser_ms = (now_ms - info['send_ms']) / 1000.0
                info_tag = info_tag + " {:.2f}s, {:.2f}s".format(
                                            total_ms, browser_ms )

            msg = "|BROWSER {} {} {} {}\n| {}\n| {}".format(
                        msg_type, request.mpipname,
                        payload.get('url'), payload.get('items')[:SANITY_SIZE],
                        request.META['HTTP_USER_AGENT'], info_tag )

            # These generate emails for immediate review
            if msg_type.startswith('FATAL'):
                log.error( msg )
            elif _triggered( msg_type, msg, _warning_triggers, _warning_ignores ):
                log.warning( msg )
            # Otherwise log message for historical review
            else:
                log.info( msg )

        except KeyError:
            log.info("SUSPECT - No type in browser_message")
        except Exception:
            log.exception("Error in browser_message")

    return respond_api_call( request, handler, methods=['POST'] )

def _triggered( msg_type, msg, triggers, ignores ):
    msg_type = msg_type.lower()
    msg = msg.lower()
    return any( msg_type.startswith( trigger ) for trigger in triggers
                ) and not any( ignore in msg for ignore in ignores )

_warning_triggers = [ trigger.lower() for trigger in
                        settings.MP_LOG_BROWSER.get('WARNING_TRIGGERS', []) ]
_warning_ignores = [ ignore.lower() for ignore in
                        settings.MP_LOG_BROWSER.get('WARNING_IGNORES', []) ]

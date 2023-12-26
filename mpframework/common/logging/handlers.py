#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF logging handlers
"""
import sys
import logging
from django.conf import settings
from django.views.debug import ExceptionReporter
from django.template import Engine
from django.template import Context


ENGINE = Engine()

# Can't reference settings on load so wrap in lamdas
FROM_ADDRESS = lambda: settings.DEFAULT_FROM_EMAIL
TO_ADDRESS = lambda: [ admin[1] for admin in settings.ADMINS ]


class mpEmailErrorHandler( logging.Handler ):
    """
    Replacement for Django AdminEmailHandle logging handler
    Uses mpExceptionReporter to cut down the Django info sent error emails
    """
    priority = 'MS'

    def emit( self, record ):
        text_message = record.getMessage()
        title = text_message[:80]
        html_message = None

        # Get request and exception info if present
        try:
            request = record.request
        except Exception as e:
            request = None
        try:
            if record.exc_info:
                reporter = mpExceptionReporter( request, is_email=True,
                            *record.exc_info )
                if getattr( settings, 'MP_ERROR_EMAIL_HTML', None ):
                    html_message = reporter.get_traceback_html()
                else:
                    text_message = reporter.get_traceback_text()
        except Exception as e:
            text_message = "ERROR creating logging email: %s" % e

        from ..email import send_email
        send_email( title, text_message, FROM_ADDRESS(), TO_ADDRESS(),
                    html_message=html_message, priority=self.priority )


class mpEmailErrorDirectHandler( mpEmailErrorHandler ):
    priority = 'NOW'


class mpEmailInfoHandler( logging.Handler ):
    """
    Used for non-error logging emails, to provide logging emails to root staff
    """

    def emit( self, record ):
        """
        Create nicer info email than the Django default
        """
        log_message = record.getMessage()
        try:
            request = record.request
        except Exception as e:
            request = None

        try:
            template = ENGINE.from_string( EMAIL_INFO_TEMPLATE )

            from ..utils import now
            context = Context({
                'message': log_message,
                'request': request,
                'server_time': now(),
                })

            message = template.render( context )

        except Exception as e:
            message = "ERROR creating logging email: %s" % e

        from ..email import send_email
        title = log_message[:60]
        send_email( title, log_message, FROM_ADDRESS(),
                    TO_ADDRESS(), html_message=message )

EMAIL_INFO_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8">
    <title>Logging</title>
    <style type="text/css">
      html * { padding:0; margin:0; }
      body * { padding:10px 20px; }
      body * * { padding:0; }
      body { font:small sans-serif; }
      h1 { font-weight:normal; }
      </style>
    </head>
  <body>
    <h1>{{ message }}</h1>
    <div>Server time: {{ server_time|date:"r" }}</div>
    </body>
  </html>
"""

#-----------------------------------------------------------------------------

from django.template import TemplateDoesNotExist
from django.template.defaultfilters import pprint
from django.utils import timezone
from django.utils.encoding import force_str
from django import get_version

class mpExceptionReporter( ExceptionReporter ):
    """
    Override exception reporter to suppress amount of settings
    and request info in admin/dev emails
    """

    def get_traceback_data( self ):
        """
        Cherry pick info from Django since no good hooks to modify message;
        this is used for both Django errors and MPF logging
        """
        if self.exc_type and issubclass(self.exc_type, TemplateDoesNotExist):
            self.template_does_not_exist = True
            self.postmortem = self.exc_value.chain or [self.exc_value]

        frames = self.get_traceback_frames()
        for i, frame in enumerate(frames):
            if 'vars' in frame:
                frame_vars = []
                for k, v in frame['vars']:
                    v = pprint(v)
                    # Trim large blobs of data
                    if len(v) > 4096:
                        v = '%s… <trimmed %d bytes string>' % (v[0:4096], len(v))
                    frame_vars.append((k, v))
                frame['vars'] = frame_vars
            frames[i] = frame

        unicode_hint = ''
        if self.exc_type and issubclass(self.exc_type, UnicodeError):
            start = getattr(self.exc_value, 'start', None)
            end = getattr(self.exc_value, 'end', None)
            if start is not None and end is not None:
                unicode_str = self.exc_value.args[1]
                unicode_hint = force_str(
                    unicode_str[max(start - 5, 0):min(end + 5, len(unicode_str))],
                    'ascii', errors='replace'
                )

        if self.request is None:
            user_str = None
        else:
            try:
                user_str = str(self.request.user)
            except Exception:
                # request.user may raise OperationalError if the database is
                # unavailable, for example.
                user_str = '[unable to retrieve the current user]'

        c = {
            'is_email': self.is_email,
            'unicode_hint': unicode_hint,
            'frames': frames,
            'request': self.request,
            'user_str': user_str,
            'server_time': timezone.now(),
            'django_version_info': get_version(),
            'sys_version_info': '%d.%d.%d' % sys.version_info[0:3],
            'template_info': self.template_info,
            'template_does_not_exist': self.template_does_not_exist,
            'postmortem': self.postmortem,
            # Don't care about these items, but not worth blanking in template
            'sys_path': 'MPF',
            'sys_executable': 'MPF',
            }
        if settings.DEBUG:
            c['settings'] = self.filter.get_safe_settings()
            c['request_meta'] = self.filter.get_safe_request_meta(self.request)

        if self.request is not None:
            c['filtered_POST_items'] = list(self.filter.get_post_parameters(self.request).items())
            c['request_GET_items'] = self.request.GET.items()
            c['request_FILES_items'] = self.request.FILES.items()
            c['request_COOKIES_items'] = self.request.COOKIES.items()
        # Check whether exception info is available
        if self.exc_type:
            c['exception_type'] = self.exc_type.__name__
        if self.exc_value:
            c['exception_value'] = str(self.exc_value)
        if frames:
            c['lastframe'] = frames[-1]

        return c

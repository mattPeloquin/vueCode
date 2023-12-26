#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support links on the helper calls screen, which
    has links that don't require extra info.
"""
from django.conf import settings
from django.http import Http404
from django.http import HttpResponseRedirect
from django.urls import get_callable
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.view import root_only
from mpframework.common.email import send_email_user
from mpframework.common.tasks.tests import test_task
from mpframework.common.tasks.tests import test_job
from mpframework.common.deploy.server import get_uwsgi
from mpframework.common.utils import timestamp


@root_only
def mptest_helper_calls( request ):
    return TemplateResponse( request, 'root/test/helper_calls.html', {} )

@root_only
def mptest_exc_view( request ):
    raise Exception("Testing a generic view exception!")

@root_only
def mptest_exc_404( request ):
    raise Http404("Testing a 404 view exception!")

@root_only
def mptest_logging( request, **kwargs ):
    logfn = getattr( log, kwargs.get('log') )
    logfn('TEST LOGGING MESSAGE: %s', logfn)
    return TemplateResponse( request, 'root/test/helper_calls.html', {} )

@root_only
def mptest_popup( request ):
    url_to_popup = '/' + '/'.join( request.mppathsegs[4:] ) + '?_popup=1'
    return HttpResponseRedirect( url_to_popup )

@root_only
def mptest_csrf( request ):
    """
    Test custom csrf page
    """
    return get_callable( settings.CSRF_FAILURE_VIEW )( request )

@root_only
def mptest_email( request, **kwargs ):
    """
    Template defines various email sending scenarios
    """
    num = int( kwargs.get('num', 1) )
    counter = 0
    while counter < num:
        send_email_user( request.user, "Test email: %s -> %s" % (counter, timestamp()), "That's all" )
        counter += 1
    return TemplateResponse( request, 'root/test/helper_calls.html', {} )

@root_only
def mptest_uwsgi( request, **kwargs ):
    uwsgi = get_uwsgi()
    if uwsgi:
        command = kwargs.pop('command', '')
        if command == 'RELOAD':
            uwsgi.reload()
    return TemplateResponse( request, 'root/test/helper_calls.html', {} )

#--------------------------------------------------------------------

@root_only
def mptest_task( request, **kwargs ):
    """
    Single task execution based on template values
    """
    num = int( kwargs.pop('num', 1) )
    counter = 0
    while counter < num:
        message = "Test task: %s -> %s, %s" % (
                        counter, request.mpipname, timestamp() )
        test_task( message, **kwargs )
        counter += 1
    return TemplateResponse( request, 'root/test/helper_calls.html', {} )

@root_only
def mptest_job( request, **kwargs ):
    """
    Job task hierarchy execution based on template values
    """
    num = int( kwargs.pop('num', 1) )
    for n in range( num ):
        msg = "Test job: %s -> %s, %s" % ( n, request.mpipname, timestamp() )
        test_job( msg, **kwargs )
    return TemplateResponse( request, 'root/test/helper_calls.html', {} )

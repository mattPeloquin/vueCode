#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support forms on the helper forms screen.
"""
from django import forms
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.view import root_only
from mpframework.common.email import send_email_sandbox


class _EmailForm( forms.Form ):
    frm = forms.CharField( required=False, label="Override support FROM email" )
    to = forms.CharField( required=False, label="Optional comma separated TO" )
    subject = forms.CharField( required=False, label="Subject line" )
    html = forms.BooleanField( required=False, label="Body is HTML" )
    body = forms.CharField( required=False,
                widget=forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
                label="Text or HTML body")


@root_only
def mptest_helper_forms( request ):
    """
    Support test helper urls
    Used to have a form here for test options, but wasn't needed
    """

    # Email form
    if 'email' in request.POST:
        email_form = _EmailForm( request.POST )
        if email_form.is_valid():
            data = email_form.cleaned_data
            log.info("TEST HELPER sending email: %s", data)
            to = data.get('to')
            if to:
                to = to.split(',')
            body = data.get('body')
            html = body if data.get('html') else None

            send_email_sandbox( request.sandbox, data.get('subject'), body,
                        from_email=data.get('frm'), to_emails=to,
                        html_message=html )
    else:
        email_form = _EmailForm()

    return TemplateResponse( request, 'root/test/helper_forms.html', {
                'email_form': email_form,
                })

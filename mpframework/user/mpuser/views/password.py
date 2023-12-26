#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    The views below utilize Django built-in views for logout,
    password change/reset, etc. using MPF templates
"""
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.utils.decorators import method_decorator

from mpframework.common import log
from mpframework.common.view import ssl_required
from mpframework.common.view import login_required

from ..forms.password import SetPasswordForm
from ..forms.password import ResetPasswordForm


class mpPasswordChangeDoneView( auth_views.PasswordChangeDoneView ):
    """
    Profile screen password change done
    """
    template_name = 'user/password/change_done.html'

    @method_decorator( ssl_required )
    @method_decorator( login_required )
    def dispatch( self, request, *args, **kwargs ):
        log.debug2("%s change password done", request.user)
        return super().dispatch( request, *args, **kwargs )

#---------------------------------------------------------------
#  Password reset views

class mpPasswordResetView( auth_views.PasswordResetView ):
    """
    Display reset password page to visitor
    Delegates to Django, but implements tenancy and carrying
    email from login page.
    """
    form_class = ResetPasswordForm
    template_name = 'user/password/reset.html'
    email_template_name = 'user/password/reset_email_text.html'
    html_email_template_name = 'user/password/reset_email_html.html'
    success_url = reverse_lazy('pwd_reset_sent')

    def dispatch( self, request, *args, **kwargs ):
        log.debug("Password confirmation for %s", request.user)

        if request.method == 'POST':
            log.info("Password reset request: %s -> %s",
                    request.sandbox, request.POST.get('email', ''))
            # HACK - add sandbox to post so it is available django-derived forms
            request.POST._mutable = True
            request.POST['sandbox'] = request.sandbox

        return super().dispatch( request, *args, **kwargs )

    def get_context_data( self, **kwargs ):
        context = super().get_context_data( **kwargs )
        context.update({
            'no_robots': True,
            **(self.extra_context or {})
            })
        if self.request.method != 'POST':
            email_from_login = self.request.GET.get( 'email', '' )
            context.update({
                'email_from_login': email_from_login,
                'scheme': self.request.scheme,
                })

        return context


class mpPasswordResetSentView( auth_views.PasswordResetDoneView ):
    template_name = 'user/password/reset_sent.html'


class mpPasswordResetCompleteView( auth_views.PasswordResetCompleteView ):
    template_name = 'user/password/reset_complete.html'


class mpPasswordResetConfirmView( auth_views.PasswordResetConfirmView ):
    form_class = SetPasswordForm
    template_name = 'user/password/reset_confirm.html'
    success_url = reverse_lazy('pwd_reset_complete')

    def dispatch( self, request, *args, **kwargs ):
        log.debug("Password confirmation for %s", request.user)
        kwargs['uidb64'] = kwargs.pop('user_id_b64')
        return super().dispatch( request, *args, **kwargs )

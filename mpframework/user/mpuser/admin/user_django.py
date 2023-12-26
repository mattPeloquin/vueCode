#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django user mixin
"""
from django.urls import re_path
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.contrib import admin, messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.admin.utils import unquote
from django.contrib.admin.options import IS_POPUP_VAR
from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.utils.html import escape
from django.utils.translation import gettext

from mpframework.common import _


class DjangoPasswordAdminMixin:
    """
    Code from Django's contrib/auth/admin.py for managing password change;
    there wasn't a good way to include the Django code and inherit from
    NestedAdmin, so relevant parts are copied here.
    """
    change_password_form = AdminPasswordChangeForm

    def clean_password( self ):
        """
        Since pwd should never be shown/changed in user form, regardless of
        what might get sent from a post, return the initial pwd value.
        This is done here, rather than on the field, because the
        field does not have access to the initial value.
        """
        return self.initial.get('password')

    def get_urls( self ):
        return [
            re_path( r'^(.+)/password[/]?$',
                        self.admin_site.admin_view(self.user_change_password),
                        name='auth_user_password_change',
            ),
        ] + super().get_urls()

    def lookup_allowed( self, lookup, value ):
        # See #20078: we don't want to allow any lookups involving passwords.
        if lookup.startswith('password'):
            return False
        return super().lookup_allowed( lookup, value )

    def user_change_password(self, request, id, form_url=''):
        user = self.get_object(request, unquote(id))
        if not self.has_change_permission(request, user):
            raise PermissionDenied
        if user is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
                'name': self.model._meta.verbose_name,
                'key': escape(id),
            })
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, user, change_message)
                msg = gettext('Password changed successfully.')
                messages.success(request, msg)
                update_session_auth_hash(request, form.user)
                return HttpResponseRedirect(
                    reverse(
                        '%s:%s_%s_change' % (
                            self.admin_site.name,
                            user._meta.app_label,
                            user._meta.model_name,
                        ),
                        args=(user.pk,),
                    )
                )
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            'title': _('Change password: %s') % escape(user.get_username()),
            'adminForm': adminForm,
            'form_url': form_url,
            'form': form,
            'is_popup': (IS_POPUP_VAR in request.POST or
                         IS_POPUP_VAR in request.GET),
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
            **self.admin_site.each_context(request),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.change_user_password_template or
            'admin/auth/user/change_password.html',
            context,
        )

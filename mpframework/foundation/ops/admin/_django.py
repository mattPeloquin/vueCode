#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Expose some Django internal tables
"""
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

from mpframework.common.admin import root_admin
from mpframework.common.admin.base_model import BaseAdmin


class LogEntryAdmin( BaseAdmin ):
    no_tenant_filter = True
    list_display = ('user', 'content_type', 'change_message', 'object_repr', 'object_id' )
    list_filter = ('content_type', 'change_message')
    list_add_root = ()
    # SCALE - can't display all users
    readonly_fields = ('user',)

root_admin.register( LogEntry, LogEntryAdmin )


class ContentTypeAdmin( BaseAdmin ):
    no_tenant_filter = True
    ordering = ('app_label', 'model')
    list_display = ('app_label', 'model')
    list_filter = ('app_label',)
    list_add_root = ()

root_admin.register( ContentType, ContentTypeAdmin )

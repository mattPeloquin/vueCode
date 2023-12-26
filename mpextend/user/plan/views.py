#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Views to support plan functionality
"""
from django.template.response import TemplateResponse

from mpframework.common.cache.template import full_path_cache
from mpextend.product.account.group import group_admin_view


@full_path_cache
@group_admin_view
def ga_plans( request, account ):

    # FUTURE - GA admin plan management

    return TemplateResponse( request, 'group/plans.html', {
                })

@full_path_cache
def user_plans( request ):

    # FUTURE - user profile plan management

    return TemplateResponse( request, 'user/profile/plans.html', {
                })

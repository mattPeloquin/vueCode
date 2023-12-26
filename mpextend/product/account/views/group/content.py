#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Group account admin content usage
"""
from django.template.response import TemplateResponse
from django.contrib.contenttypes.models import ContentType

from mpframework.common import log
from mpframework.common.cache.template import full_path_cache
from mpframework.user.mpuser.models import mpUser
from mpextend.user.usercontent.models import UserItem

from ...group import group_admin_view
from ._common import ga_admin_common


@full_path_cache
@group_admin_view
def ga_content( request, account ):
    """
    Screen with top-collection summary of content and report buttons
    """
    account, context = ga_admin_common( request, account )
    user_ids = account.user_ids

    # Get summary of top-level collection and item usage
    trees = {}
    items = {}
    tops = UserItem.objects\
                    .mpusing('read_replica')\
                    .select_related( 'cu', 'item' )\
                    .filter( sandbox=request.sandbox, cu__user_id__in=user_ids,
                             top_tree__isnull=True,
                             uses__gte=1 )
    for ui in tops.values( 'item___name', 'item___django_ctype_id',
                            'progress', 'seconds_used' ).iterator():
        try:
            is_tree = ContentType.objects.get_for_id(
                                ui['item___django_ctype_id'] ).model == 'tree'
            _accumulate_totals( ui, trees if is_tree else items )

        except Exception as e:
            log.warning_quiet("Error in GA usage aggregation: %s -> %s", ui, e)

    context.update({
            'collections': trees,
            'items': items,
            })
    return TemplateResponse( request, 'group/content.html', context )

def _accumulate_totals( ui, content ):
    name = ui['item___name']
    tc = content.get( name, { 'started': 0, 'completed': 0, 'minutes': 0 } )
    content[ name ] = {
        'started': tc['started'] + ( 1 if ui['progress'] in 'S' else 0 ),
        'completed': tc['completed'] + ( 1 if ui['progress'] in 'CA' else 0 ),
        'minutes': tc['minutes'] + ( ui['seconds_used'] // 60 ),
        }

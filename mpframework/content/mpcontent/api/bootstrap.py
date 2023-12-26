#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content bootstrap

    When getting data for timewin deltas, only grab items modified
    after delta time, send empty values to override blanked values,
    and get retired items to overide recently retired items.
"""

from mpframework.common import log

from ..models import PortalType
from ..models import PortalGroup
from ..models import PortalCategory
from ..models import Tree
from ..models import BaseItem
from ..models.tree_item import TreeBaseItem
from ._utils import get_common_values
from ._utils import get_baseitem_values
from ._utils import get_tree_values
from ._utils import add_value


# The groupings don't use timewin deltas

def get_portal_types( request ):
    rv = []
    for typ in PortalType.objects.get_portal_objs( request ):
        values = get_common_values( typ, full_load=True )
        add_value( values, 'scope', typ.scope )
        rv.append( values )
    return rv

def get_portal_groups( request ):
    rv = []
    for grp in PortalGroup.objects.get_portal_objs( request ):
        values = get_common_values( grp, full_load=True )
        add_value( values, 'scope', grp.scope )
        add_value( values, 'script_name', grp._script_name )
        add_value( values, 'tag_matches', grp.tag_matches )
        add_value( values, 'html', grp.html )
        add_value( values, 'nav_template',
                    grp.nav_template and grp.nav_template.script_name )
        add_value( values, 'item_template',
                    grp.item_template and grp.item_template.script_name )
        rv.append( values )
    return rv

def get_portal_categories( request ):
    rv = []
    for cat in PortalCategory.objects.get_portal_objs( request ):
        values = get_common_values( cat, full_load=True )
        add_value( values, 'scope', cat.scope )
        rv.append( values )
    return rv


# Items and Trees use timewin deltas

def get_items( request, **kwargs ):
    """
    Return list of baseitem values to send to client.
    To avoid downcasting expense, content for specializations is not sent with
    the bootstrapping process.
    This needs to be pickled, so list is returned vs. dict_values view.
    """
    items = {}
    if log.debug_on():
        rt = request.mptiming
        rt.mark()
        log.timing("%s START LOADING ITEMS %s: %s", rt.pk, rt, request.mpipname)

    # Get all items
    qs = BaseItem.objects.mpusing('read_replica')\
                .select_related( None )\
                .exclude( _django_ctype__model='tree' )
    qs, send_empty = _fixup_queryset( qs, request, **kwargs )
    full_load = request.sandbox.options['bootstrap.content_full_load']

    # Setup values for sending via JSON
    for item in qs.iterator():
        load_all = full_load or item.sb_options['bootstrap.content_full_load']
        items[ item.id ] = get_baseitem_values( item, send_empty,
                    full_load=load_all )
    # Add any categories
    for id, categories in _get_categories( list(items) ).items():
        add_value( items[ id ], 'portal_categories', categories )

    log.debug_on() and log.debug("%s FINISHED LOADING ITEMS(%s) %s: %s items",
                                    rt.pk, rt.log_recent(), rt, len(items))
    return list( items.values() )

def get_trees( request, **kwargs ):
    """
    Tree nodes (collections) are focal point of content display.
    This key method for loading the portal is optimized to limit DB impact
    when there are a large number of tree nodes. Unlike items, every tree
    node needs to be processed twice, so just loop array.
    """
    rv = []
    if log.debug_on():
        rt = request.mptiming
        rt.mark()
        log.timing("%s START LOADING TREES %s: %s -> %s",
                        rt.pk, rt, request.mpipname, kwargs)

    qs = Tree.objects.mpusing('read_replica')\
                .select_related('baseitem_ptr')
    qs, send_empty = _fixup_queryset( qs, request, **kwargs )
    full_load = request.sandbox.options['bootstrap.content_full_load']

    # Map tree node values and doing some first-pass processing on
    # the tree list to allow lookups to reduce DB hits
    tree_node_ids = []
    tree_roots = {}

    for node in qs.iterator():
        log.detail3("Tree node: %s -> %s, %s", node.pk, node.tag, node.name)
        load_all = full_load or node.sb_options['bootstrap.content_full_load']

        tree = get_tree_values( node, send_empty, full_load=load_all )

        # Save each tree node id to allow base items in one DB hit below
        tree_node_ids.append( node.pk )

        # Capture MPTT tree id in values root as a placeholder, and id for
        # any roots in dictionary keyed on MPTT tree ID. Allows assigning root
        # tree node to all members of a tree in second pass.
        tree_id = node._mpttfield('tree_id')
        tree['my_root'] = tree_id
        if not node.parent_id:
            tree_roots[ tree_id ] = node.pk

            # Add any descendant node ids to the values
            tree['all_nodes'] = node.get_descendant_ids

        rv.append( tree )

    log.debug_on() and log.debug2("%s %s - Loading trees part 1: %s tree nodes",
                                    rt.pk, rt, len(rv))

    # Now get every tree_item for the tree nodes into a dict indexed by
    # the tree id; so one DB fetch for all item ids associated with the trees
    node_treeitems = {}
    node_treeitems_ids = {}
    for ti in TreeBaseItem.objects.mpusing('read_replica')\
                    .filter( tree_id__in=tree_node_ids )\
                    .values( 'tree_id', 'item_id', 'area', 'is_required', 'drag_order',
                            'item___name', 'item__tag', 'item__hist_modified' )\
                    .iterator():
        node_treeitems.setdefault( ti['tree_id'], [] ).append( ti )
        node_treeitems_ids.setdefault( ti['tree_id'], [] ).append( ti['item_id'] )

    treecat_ids = _get_categories( tree_node_ids )

    # Then add tree node information and tree_items
    for tree in rv:
        tree_id = tree['id']

        # Add the root for this tree from the root nodes stored on first pass
        # Gracefully handle MPTT tree out of whack by saying bad node is a root
        try:
            root_id = tree_roots[ tree['my_root'] ]
        except KeyError:
            log.warning_quiet("Collection MPTT NO ROOT (workflow?): %s -> %s,%s -> %s",
                    request.sandbox, tree_id, tree['my_root'], tree['name'] )
            root_id = tree_id

        tree['my_root'] = root_id

        # Add categories
        add_value( tree, 'portal_categories', treecat_ids.get( tree_id ) )

        # Add item area relationships to send to client
        tree_items = node_treeitems.get( tree_id )
        if tree_items:
            _add_tree_items( tree, tree_items )

        # For root collections, send all descendant ids
        if not tree.get('parent'):
            all_items = node_treeitems_ids.get( tree_id, [] )
            for node_id in tree['all_nodes']:
                all_items.extend( node_treeitems_ids.get( node_id, [] ) )
            tree['all_items'] = all_items

    log.debug_on() and log.debug("%s FINISHED LOADING TREES(%s) %s: %s trees",
                                    rt.pk, rt.log_recent(), rt, len(rv))
    return rv

def _get_categories( ids ):
    # Get set of all category MTM records in one DB hit
    # DON'T use read replica since the through table doesn't use MPF queryset
    cat_ids = {}
    for icat in BaseItem.portal_categories.through.objects\
                    .filter( baseitem_id__in=ids )\
                    .iterator():
        cat_ids.setdefault( icat.baseitem_id, [] ).append( icat.portalcategory_id )
    return cat_ids

def _add_tree_items( tree, tree_items ):

    # Provide default sort each according to item order
    opts = tree.get('options')
    order = opts and opts.get('portal.item_order')
    if order:
        if 'tag' == order:
            tree_items.sort( key=lambda ti:( ti['item__tag'], ti['item__tag'] ) )
        elif 'modified' == order:
            tree_items.sort( key=lambda ti:( ti['item__hist_modified'] ) )
        elif 'available' == order:
            tree_items.sort( key=lambda ti:( ti['item___available'] ) )
        else:
            tree_items.sort( key=lambda ti: ti['item___name'] )
    else:
        tree_items.sort( key=lambda ti: ti['drag_order'] )

    # Add area and required flag
    areas = {}
    required = []
    for ti in tree_items:
        try:
            if ti['is_required']:
                required.append( ti['item_id'] )
            areas.setdefault(
                    TreeBaseItem.AREA_DICT[ ti['area'] ], []
                    ).append( ti['item_id'] )
        except KeyError:
            log.warning("ERROR DATA - could not add tree item %s", str(ti))
    add_value( tree, 'items_required', required )
    for area, item_ids in areas.items():
        add_value( tree, 'items_' + area, item_ids )

def _fixup_queryset( qs, request, **kwargs ):
    """
    Shared code to adjust item and tree querysets based on timewin delta
    """
    delta = kwargs.pop('delta', False)
    if delta:
        qs = qs.filter( hist_modified__gte=delta )
    else:
        qs = qs.exclude( workflow__in='R' )
    return qs.filter( request=request, **kwargs ), bool(delta)

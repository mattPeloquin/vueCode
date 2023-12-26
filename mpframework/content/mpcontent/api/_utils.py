#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for marshalling client API for content items
"""


def add_value( values, name, value, empty=False ):
    """
    Add if not empty; empties are handles as defaults in client
    """
    if (empty and not value) or value:
        values[ name ] = value

def item_results( items ):
    return {
        'item_names': [ item.name for item in items ],
        'update_count': len(items),
        }

def get_common_values( item, empty=False, full_load=False ):
    """
    Load data common across all content
    """
    rv = {}
    rv['id'] = item.pk
    rv['name'] = item.name
    add_value( rv, 'image1', item.image1_url, empty )
    add_value( rv, 'image2', item.image2_url, empty )
    add_value( rv, 'text1', item.text1, empty )
    add_value( rv, 'text2', item.text2, empty )
    # Yaml text was converted to Python obj, now convert to JSON
    # Send to client as 'options' instead of 'sb_options' as it will
    # be blended with site and pane options or accessed from sb('options')
    if empty or item.sb_options:
        rv['options'] = item.sb_options
    # Only send workflow if not production
    if empty or item.workflow != 'P':
        rv['workflow'] = item.workflow

    if full_load:
        rv['hist_rev'] = item.revision
        rv['hist_modified'] = item.hist_modified

    return rv

def _tree_and_item_values( item, empty=False, full_load=False ):
    """
    Load data common across trees and items
    """
    rv = get_common_values( item, empty, full_load )

    add_value( rv, 'tag', item.tag, empty )
    add_value( rv, 'portal_type_id', item.portal_type_id, empty )
    add_value( rv, 'portal_group_id', item.portal_group_id, empty )
    add_value( rv, 'item_template', item.item_template and
                item.item_template.script_name, empty )
    add_value( rv, 'text3', item.text3, empty )
    add_value( rv, 'text4', item.text4, empty )
    add_value( rv, 'search_tags', item.search_tags.lower(), empty )
    add_value( rv, 'tooltip', item.tooltip, empty )
    add_value( rv, 'available', item.available, empty )
    add_value( rv, 'size', item.size, empty )
    add_value( rv, 'points', item._points, empty )
    # Slug can be set or defaults to id on client
    add_value( rv, 'slug', item._slug, empty )
    if full_load:
        rv['more_to_load'] = False
        add_value( rv, 'html1', item.html1, empty )
        add_value( rv, 'html2', item.html2, empty )
        add_value( rv, 'html3', item.html3, empty )
    else:
        rv['more_to_load'] = bool(item.html1 or item.html2 or item.html3)

    return rv

def get_baseitem_values( item, empty=False, full_load=False ):
    """
    Load data for items
    """
    rv = _tree_and_item_values( item, empty, full_load )
    rv['type_db'] = item.type_db

    # HACK - Only send downcast items if different than default
    action = item.access_action
    if empty or ( action and action != 'action_viewer' ):
        rv['action'] = action
    type_view = item.type_view()
    if empty or ( type_view != item.type_db ):
        rv['type_view'] = type_view
    if item.type_db != item.type_name:
        rv['type_name'] = item.type_name
    if item.content_rev > 1:
        rv['content_rev'] = item.content_rev
    return rv

def get_tree_values( node, empty=False, full_load=False ):
    """
    Load data for items
    """
    rv = _tree_and_item_values( node, empty, full_load )
    rv['type_db'] = 'tree'
    rv['type_name'] = u"Collection"
    rv['parent'] = node.parent_id or ''
    rv['depth'] = node.mptt_level
    if node.is_top:
        add_value( rv, 'panel', node.panel and node.panel.script_name, empty )
        add_value( rv, 'bg_image', node.background_image_url, empty )
    add_value( rv, 'nav_template', node.nav_template and
                node.nav_template.script_name, empty )
    add_value( rv, 'children', node.get_children_ids, empty )
    add_value( rv, 'node_template', node.node_template and
                node.node_template.script_name, empty )
    add_value( rv, 'viewer', node.viewer and node.viewer.script_name, empty )
    add_value( rv, 'image3', node.image3_url, empty )
    add_value( rv, 'image4', node.image4_url, empty )
    return rv

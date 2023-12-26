/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Staff content support for portal and other screens.

    Duck-typed item objects are used either for portal models/vms
    or other objects with type_db, id, and tree_id
*/
(function() { 'use strict';

    mp.content_edit = function( item, event, popup ) {
    /*
        Provide redirection to/from admin edit page for a content item
    */
        event.stopPropagation()
        if( item && item.type_db && item.id ) {
            let admin_name = item.type_db
            if( admin_name == 'tree' ) {
                admin_name = item.depth ? 'treenested' : 'treetop'
                }
            mp.staff_edit( admin_name, item.id, popup )
            }
        }

    mp.content_copy = function( item, event ) {
    /*
        Clone item, add to parent collection, and open editing page
    */
        event.stopPropagation()
        if( item && item.type_db && item.id ) {
            _add_collection( event.target, item )
            }
        }

    mp.content_addcollection = function( element, name ) {
    /*
        Create a new empty object in the collection, and then
        open editing screen for it.
    */
        // If there is an admin save, save sollection first
        $('#mpsavecontinue').click()
        _add_collection( element, name )
        }

    mp.content_find_tree_id = function( element ) {
    /*
        For non-portal screens (admin), find parent only based DOM
        check for parent mp_tree_node.
    */
        return $( element ).parents(".mp_tree_node").data('content_id')
        }

    function _add_collection( element, item ) {
    /*
        Shared code to add either a new item (if item is a string),
        or clone of an existing item (if item is a vm)
        Will add to tree node that is closest parent, if present
    */
        if( item ) {
            const item_data = {}
            item_data.tree_id = mp.content_find_tree_id( element )

            let item_type = null
            if( _.isString( item ) ) {
                item_data.item_type = item
                item_type = item
                }
            else {
                item_data.clone_id = item.id
                item_type = item.type_db
                }

            if( item_type ) {
                mp.fetch({
                    url: mpurl.api_item_add,
                    method: 'POST',
                    data: item_data,
                    wait_indicator: true,
                    finished: function( values ) {
                        mp.staff_edit( item_type, values['new_item_id'] )
                        }
                    })
                }
            }
        }

    })();

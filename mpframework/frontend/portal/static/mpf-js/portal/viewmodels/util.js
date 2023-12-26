/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Utilities specific to Viewmodels
*/
(function() { 'use strict';

    mpp.item_name = function( item, default_name ) {
        return item ? item.name : ( default_name || '' )
        }

    /*---------------------------------------------------------------
       Support for prev-next in viewmodel collections
    */

    // Get next or prev node based on current node's root tree relationship
    mpp.next_node = function( node ) {
        return _traverse_node( node, true )
        }
    mpp.prev_node = function( node ) {
        return _traverse_node( node, false )
        }
    function _traverse_node( node, forward ) {
        node === undefined && ( node = mpp.vm_current.node() )
        let new_node = false
        if( node && node.id ) {
            new_node = forward ? node.next_node() : node.prev_node()
            }
        return new_node
        }

    // Returns the prev/next item in the current node (based on current item)
    // Or first item in passed-in node, if available
    // Optionally executes function passed in with current node and next item
    mpp.next_core_item = function( fn, node, current_item ) {
        return _traverse_core_item( fn, true, node, current_item )
        }
    mpp.prev_core_item = function( fn, node, current_item ) {
        return _traverse_core_item( fn, false, node, current_item )
        }
    function _traverse_core_item( fn, forward, node, current_item ) {
        let new_item = false
        if( node && node.id ) {
            new_item = forward ? node.next_core() : node.prev_core()
            }
        else {
            node = mpp.vm_current.node()
            if( node && node.id ) {
                current_item = current_item || mpp.vm_current.item()
                new_item = forward ? node.next_core( current_item ) : node.prev_core( current_item )
                }
            }
        if( !new_item ) {
            new_item = _traverse_node_core_item( fn, node, forward )
            }
        else if( fn ) {
            fn( new_item, node )
            }
        return new_item
        }

    // Returns next/prev core item from next/prev node
    mpp.next_node_core_item = function( fn, node ) {
        return _traverse_node_core_item( fn, node, true )
        }
    mpp.prev_node_core_item = function( fn, node ) {
        return _traverse_node_core_item( fn, node )
        }
    function _traverse_node_core_item( fn, node, forward ) {
        let new_item = false
        const new_node = forward ? mpp.next_node( node ) : mpp.prev_node( node )
        if( new_node ) {
            new_item = _traverse_core_item( fn, forward, new_node )
            }
        return new_item
        }

    // Shared code for finding next item in collection
    mpp.traverse_item = function( collection, current, forward ) {
        let rv = false
        let prev_item = false
        let current_found = false
        _.some( collection, function( item ) {
            // If current item not defined, first is returned
            if( !current ) {
                rv = item
                return true
                }
            // If current found on previous path, time to exit
            if( current_found ) {
                rv = forward ? item : prev_item
                return true
                }

            current_found = ( item.id == current.id )

            if( !current_found ) {
                prev_item = item
                }
            })
        return rv
        }

    /*---------------------------------------------------------------
        Safe calls to get underlying model from DOM

        Avoid LookBeforeYouLeap boilerplate when asking a
        UI element if it represents a model.
    */

    mpp.get_model = function( element ) {
        return mpp.get_models( element )[0]
        }

    mpp.get_models = function( elements ) {
        let rv = []
        $( elements ).each( function() {
                try {
                    const vm = ko.dataFor( this )
                    rv.push( vm.model )
                    }
                catch( e ) {
                    mp.log_info("No model for DOM element: ", this, " -> ", e)
                    }
                })
        return rv
        }

    })();

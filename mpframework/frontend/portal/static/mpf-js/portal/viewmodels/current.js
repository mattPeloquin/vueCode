/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Singleton VM for tracking current content item, including
    logic for the node it came frame.
*/
(function() { 'use strict';

    // Simplify code with an empty VM for cases when no current items
    function _empty_item() {
        return new mpp.VmShared()
        }

    mpp.vm_current = _.extend( mpp.vm_current || {}, {

        // Observers for UI decisions based on current selection
        node: ko.observable( _empty_item() ),
        item: ko.observable( _empty_item() ),

        node_set: function( node ) {
            if( !node ) {
                this.node( _empty_item() )
                }
            else if( ko.unwrap( this.node ) != node.id ) {
                this.node( node )
                }
            return this.node()
            },

        // There is always an active node navigation, but
        // active items come and go. Provide some logic for keeping track
        item_set: function( item ) {
            const current_item = this.item()
            if( current_item.id != item.id ) {
                this.prev_item = current_item
                this.item( item )
                }
            return this.item()
            },
        prev_item: _empty_item(),
        item_clear: function() {
            this.item_set( _empty_item() )
            },

        // Convenience accessors
        root: function() {
            const node = this.node()
            if( node && node.id ) {
                return node.my_root()
                }
            },

        // Access attribute with node or root defaults
        // Separate item from node/root to avoid triggering item observable change
        get_node_root: function( attr ) {
            const node = this.node().model
            if( node && node.get && node.get( attr ) ) {
                return node.get( attr )
                }
            const root = this.root()
            if( root ) {
                return root.model.get( attr )
                }
            },
        get_item_node_root: function( attr, item ) {
            item = item || this.item().model
            if( item && item.get && item.get( attr ) ) {
                return item.get( attr )
                }
            return this.get_node_root( attr )
            },
        get_prev_item_node_root: function( attr ) {
            return this.get_item_node_root( attr, this.prev_item.model )
            },

        logname: function() { return 'VM-current' },
        })

    })();

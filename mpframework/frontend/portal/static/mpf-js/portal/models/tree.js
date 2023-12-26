/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Collection/Tree node model
*/
(function() { 'use strict';

    mpp.Tree = mpp.ItemBase.extend({
    /*
        Client side representation of tree/collection nodes
        Provides support for managing children and items in sub trees.
    */

        initialize: function() {
            const self = this
            mpp.ItemBase.prototype.initialize.apply( self, arguments )
            _.extend( self._filter_groups, {
                    'is_tree_node': function() { return !this.is_root() },
                    })
            },

        // Tree hierarchy
        is_root: function() { return this.get('parent') === '' },
        my_root: function() { return this.get('my_root') },
        get_root: function() { return mpp.models.trees.get( this.my_root() ) },
        node_children: function() { return this.get('children') },

        // Node items and item area groupings
        items_core: function() { return this.get('items_core') || [] },
        items_required: function() { return this.get('items_required') || [] },
        items_area: function( area ) { return this.get( 'items_' + area ) || [] },

        // These are always sent to client for roots
        all_children: function() { return this.is_root() ? this.get('all_nodes') : [] },
        all_items: function() { return this.is_root() ? this.get('all_items') : [] },

        // Go all the way down the tree IF tree is a root node
        all_core: function() { return this._get_tree('items_core') },
        all_required: function() { return this._get_tree('items_required') },
        all_support: function() { return this._get_tree('items_support') },

        all_to_complete: function() {
            // If ANY required items, completion based on required, otherwise all
            return this.all_required() || this.all_items()
            },

        in_status_group: function( status ) {
            // Returns true if any items in the tree match the status
            // Possible to have id references to items not sent to client
            // due to bad data or if workflow is filtered, so don't assume ID is good
            return _.some( this.all_items(), function( item_id ) {
                            const item = mpp.models.items.get( item_id )
                            return item && _.includes( status, item.get('status') )
                            })
            },

        sb_option: function( name, element ) {
            // Nodes look up to their root for option defaults
            // Add guard recrusing messed up tree data, to avoid hanging client
            return mpp.ItemBase.prototype.sb_option.apply( this, arguments ) ||
                        ( !this.is_root() && this.get_root() != this &&
                            this.get_root().sb_option( name, element ) )
            },

        size: function() {
            // TBD - client tree size rollup
            },

        // Values won't be sent over wire if empty
        defaults: function() {
            return _.extend( mpp.ItemBase.prototype.defaults.call( this ), {
                'scope': 'C',
                'parent': '',
                'depth': 0,
                'children': [],
                'panel': '',
                'viewer': '',
                'nav_template': '',
                'node_template': '',
                'bg_image': '',
                'image3': '',
                'image4': '',
                })
            },

        _get_tree: function( attr ) {
        /*
            For root trees, return a union of all elements with attribute for
            this node and all child nodes.
        */
            return this.is_root() ? this._get_tree_array( attr ) : []
            },
        _get_tree_array: function( attr ) {
            // Recursively cache all child IDs for each node, backing up from tree leaves
            const cache_name = this.id + attr
            if( !this._tree_arrays[ cache_name ] ) {
                let children = []
                this.get('children').forEach( function( child_id ) {
                    const child = mpp.models.trees.get( child_id )
                    if( child ) {
                        children = _.union( children, child._get_tree_array( attr ) )
                        }
                    mp.log_debug_level > 2 && mp.log_debug("get_tree_array-children: ",
                            child_id, "(", child, ") - ", attr, ": ", children)
                    })

                this._tree_arrays[ cache_name ] = _.union( this.get( attr ), children )

                mp.log_debug_level > 1 && mp.log_debug("get_tree_array: ",
                        this.get('name'), " - ", attr, ": ", this._tree_arrays[cache_name])
                }
            return this._tree_arrays[ cache_name ]
            },
        _tree_arrays: {},

        })

    })();

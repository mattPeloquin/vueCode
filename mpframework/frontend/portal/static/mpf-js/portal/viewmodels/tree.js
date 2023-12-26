/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Tree/Collection ViewModel
    Provides access both to a tree node's items and children.
    Most access to items will occur through the tree accessor methods
    defined below, which are defined using wrapped functions when needed
    to force lazy evaluation.

    Node items are sorted via tree_item order field on the server, which
    is preserved in the ordering of IDs passed to the node
*/
(function() { 'use strict';

    mpp.TreeVM = function TreeVM( model ) {
        let self = Object.create( mpp.TreeVM.prototype )
        mpp.TreeVM.init( self, model )
        return self
        }

    mpp.TreeVM.init = function( self, model ) {
        mpp.ItemVM.init( self, model )
        self.type_db = 'tree'

        // ViewModel attributes that won't change, so don't need to be observables
        self.depth = model.get('depth')
        self.is_top = self.depth === 0

        // Tree VM subsets
        // Tree VMs can reference each other; these won't work until tree VMs created
        self.accessor( 'node_children', function() {
                return mpp.vm_trees().viewmodels({ 'ids': model.node_children() })
                })
        self.accessor( 'all_children', function() {
                return mpp.vm_trees().viewmodels({ 'ids': model.all_children() })
                })

        // Convenience accessors return lazy function that returns VM arrays

        self.accessor_vms('items_core')
        self.accessor_vms('items_required')
        self.accessor_vms('all_items')
        self.accessor_vms('all_core')
        self.accessor_vms('all_required')

        self.items_area = function( area ) {
            area = 'items_' + area
            self.accessor_vms( area )
            return self[ area ]()
            }
        self.all_area = function( area ) {
            area = 'all_' + area
            self.accessor_vms( area )
            return self[ area ]()
            }

        self.accessor_vms( 'portal_categories', mpp.vm_categories() )

        // Items from under this tree by tag - goes straight to vm_items
        self.accessor( 'all_tag',  function( tag ) {
                return mpp.vm_items().vm_attr(
                            { 'tag': [tag] }, { 'ids': model.all_items() })
                })
        self.accessor( 'core_tag',  function( tag ) {
                return mpp.vm_items().vm_attr(
                            { 'tag': [tag] }, { 'ids': model.all_core() })
                })

        // Match types - example of using existing accessor
        self.core_type = function( type ) {
            return self.items_core({
                model_filter: function( model ) {
                    return type == model.get('portal_type_id')
                    },
                })
            }

        // There is no base tree type, but this is expected to be available
        self._type_lookup = {}
        }
    mpp.TreeVM.prototype = _.extend( {}, mpp.ItemVM.prototype, {

        render_nav: function() {
            return true
            },
        render_item: function() {
            return false
            },

        accessor_ko_vms: function( accessor_name, vm_bag ) {
            return this.accessor_vms( accessor_name, vm_bag,
                        ko.observableArray, { notify: 'always' } )
            },

        accessor_vms: function( accessor_name, vm_bag,
                    observable_wrapper, observable_extend ) {
        /*
            Shared code for tree VM look convenience accessors, defaults
            to looking up set of IDs in the items VM bag.
        */
            const self = this
            vm_bag = vm_bag || mpp.vm_items()
            return self.accessor( accessor_name,
                    function access_vm( options ) {
                        // Call the model for ids if not provided
                        if( !options || !options.ids ) {
                            const accessor = self.model[ accessor_name ]
                            let ids = ( typeof accessor === "function" ) ?
                                    accessor.apply( self.model ) :
                                    self.model.get( accessor_name )
                            ids = ids || []
                            options = _.extend( { 'ids': ids }, options )
                            }
                        // Return VMs that match the options
                        return vm_bag.viewmodels( options )
                        },
                    observable_wrapper, observable_extend )
            },

        _css_classes: function() {
        /*
            Extend CSS types for trees
        */
            let rv = mpp.ItemVM.prototype._css_classes.call( this )
            if( this.is_top ) {
                rv += ' es_collection_top'
                }
            rv += ' mp_tree_node'
            return rv
            },

        my_root: function() {
            return mpp.vm_trees().get_id( this.model.my_root() )
            },

        /*
            Given a current node that is a child, get next/prev node if any
            from the all children list - assumes lists is sorted in hierarchy
        */
        prev_node: function() {
            return mpp.traverse_item( this.my_root().all_children(), this )
            },
        next_node: function() {
            return mpp.traverse_item( this.my_root().all_children(), this, true )
            },

        /*
            Gets next core item vm from the given item, if any
            Assumes current sorting of items core list
        */
        prev_core: function( current_item ) {
            return mpp.traverse_item( this.items_core(), current_item )
            },
        next_core: function( current_item ) {
            return mpp.traverse_item( this.items_core(), current_item, true )
            },

        // Tree nodes don't use action for now, so override base
        action: function() {
            return ''
            }
        })

    })();

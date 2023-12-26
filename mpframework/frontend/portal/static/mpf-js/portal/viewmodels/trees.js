/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Tree/Collection VM bag
*/
(function() { 'use strict';

    mpp.TreeVMs = function( models ) {
        const self = Object.create( mpp.TreeVMs.prototype )
        self.viewmodel = mpp.TreeVM
        mpp.TreeVMs.init( self, models )
        return self
        }
    mpp.TreeVM.VmBag = mpp.TreeVMs

    mpp.TreeVMs.init = function( self, models ) {
        mpp.ItemVMs.init( self, models )

        self.accessor( 'all_tops', function() {
            return self.viewmodels({ tops: true })
            })

        self.accessor( 'all_nodes', function() {
            return self.viewmodels({ filter_groups: ['is_tree_node'] })
            })
        }
    mpp.TreeVMs.prototype = _.extend( {}, mpp.ItemVMs.prototype, {

        filter_tops: function( filters, options ) {
            // Extend matches filters for common tops case
            options = _.extend( {}, options, { tops: true } )
            return this.vm_attr( filters, options )
            },

        })

    })();

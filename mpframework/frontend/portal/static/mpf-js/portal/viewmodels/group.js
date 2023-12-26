/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Portal Groups ViewModel
*/
(function() { 'use strict';

    mpp.GroupVM = function GroupVM( model ) {
        const self = Object.create( mpp.GroupVM.prototype )
        mpp.GroupVM.init( self, model )
        return self
        }

    mpp.GroupVM.init = function( self, model ) {
        mpp.VmContent.init( self, model )

        // Lazy return of array of content VMs that are in the group
        // Won't change during client lifetime, so don't need to be observable
        self.accessor( 'all_items', function( vm ) {
                vm = vm || mpp.vm_main
                return self.all_in_group( vm.all_items() )
                })
        self.accessor( 'all_tops', function( vm ) {
                vm = vm || mpp.vm_main
                return self.all_in_group( vm.all_tops() )
                })
        self.accessor( 'all_nodes', function( vm ) {
                vm = vm || mpp.vm_main
                return self.all_in_group( vm.all_nodes() )
                })
        self.accessor( 'all_content', function( vm ) {
                return _.concat( self.all_tops( vm ), self.all_items( vm ) )
                })
        }

    mpp.GroupVM.prototype = _.extend( {}, mpp.VmContent.prototype, {
        VM_ID_PREFIX: 'g',

        _css_classes: function() {
            let rv = mpp.VmContent.prototype._css_classes.call( this )
            rv += ` es_portal_group_${ this.sb('slug') }`
            return rv
            },

        in_group: function( item ) {
        /*
            Returns true if the item VM is in the group
        */
            // Does the group scope match item
            const scope = this.model.get('scope')
            if( scope == 'B' || scope == item.model.get('scope') ) {
                // Direct connection to group
                if( item.model.get('portal_group_id') == this.model.id ) {
                    return true
                    }
                // Group tag matching
                return mpp.tag_match_item( item.model, this.model.get('tag_matches') )
                }
            },

        all_in_group: function( items ) {
        /*
            Given a set of items, returns an array item VMs that are in the group
        */
            let rv = []
            const self = this
            _.each( items, function( item ) {
                if( self.in_group( item ) ) {
                    rv.push( item )
                    }
                })
            return rv
            },

        })

    })();

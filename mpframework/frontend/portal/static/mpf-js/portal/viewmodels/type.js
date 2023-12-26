/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Portal Types ViewModel
*/
(function() { 'use strict';

    mpp.TypeVM = function TypeVM( model ) {
        const self = Object.create( mpp.TypeVM.prototype )
        mpp.TypeVM.init( self, model )
        return self
        }

    mpp.TypeVM.init = function( self, model ) {
        mpp.VmContent.init( self, model )

        // Content that belong to this type
        // Won't change during client lifetime, so don't need to be observable
        self.accessor( 'all_content', function() {
                return _.concat( self.all_tops(), self.all_items() )
                })
        self.accessor( 'all_items', function() {
                return mpp.vm_items().filter_portal_type( self )
                })
        self.accessor( 'all_tops', function() {
                return mpp.vm_trees().all_tops().filter_portal_type( self )
                })
        }

    mpp.TypeVM.prototype = _.extend( {}, mpp.VmContent.prototype, {
        VM_ID_PREFIX: 't',

        _css_classes: function() {
            let rv = mpp.VmContent.prototype._css_classes.call( this )
            rv += ' es_type_' + this.sb('slug')
            return rv
            },

        })

    })();

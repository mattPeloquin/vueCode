/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Category ViewModel extensions
*/
(function() { 'use strict';

    mpp.CategoryVM = function CategoryVM( model ) {
        const self = Object.create( mpp.CategoryVM.prototype )
        mpp.CategoryVM.init( self, model )
        return self
        }

    mpp.CategoryVM.init = function( self, model ) {
        mpp.VmContent.init( self, model )

        // Tree VM subsets that belong to this category
        // Won't change during client lifetime, so don't need to be observable
        self.accessor( 'all_content', function() {
                return _.concat( self.all_tops(), self.all_items() )
                })
        self.accessor( 'all_items', function() {
                return mpp.vm_items().filter_categories([ self ])
                })
        self.accessor( 'all_tops', function() {
                return mpp.vm_trees().filter_categories([ self ])
                })
        }

    mpp.CategoryVM.prototype = _.extend( {}, mpp.VmContent.prototype, {
        VM_ID_PREFIX: 'c',

        _css_classes: function() {
            let rv = mpp.VmContent.prototype._css_classes.call( this )
            rv += ' es_category_' + this.sb('slug')
            return rv
            },

        })

    })();

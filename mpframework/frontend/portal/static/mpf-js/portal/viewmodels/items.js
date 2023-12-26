/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Item ViewModel Bag
*/
(function() { 'use strict';

    mpp.ItemVMs = function( models ) {
        const self = Object.create( mpp.ItemVMs.prototype )
        self.viewmodel = mpp.ItemVM
        mpp.ItemVMs.init( self, models )
        return self
        }
    mpp.ItemVM.VmBag = mpp.ItemVMs

    mpp.ItemVMs.init = function( self, models ) {
        mpp.VmBag.init( self, models )

        self.filter_portal_type = function( portal_type ) {
        /*
            Given a portal_type vm, return VMs that match the type
        */
            const scope = portal_type.model.get('scope')
            return self.viewmodels({
                model_filter: function( model ) {
                    if( portal_type.get_model_id() === model.get('portal_type_id') ) {
                        return scope == 'B' || scope == model.get('scope')
                        }
                    },
                })
            }

        self.filter_categories = function( categories ) {
        /*
            Given a array of category VMs return VMs whose categories
            match any of the given categories.
        */
            return self.viewmodels({
                model_filter: function( model ) {
                    return _.some( categories, function( category ) {
                        const scope = category.model.get('scope')
                        if( scope == 'B' || scope == model.get('scope') ) {
                            return _.includes( model.get('portal_categories'),
                                                category.get_model_id() )
                            }
                        })
                    },
                })
            }

        }
    mpp.ItemVMs.prototype = _.extend( {}, mpp.VmBag.prototype, {

        get_id: function( vm_id ) {
        /*
            Return VM root model id if it is in the bag
            Delegate to VM for ID resolution, to support VM ID namespaces
        */
            const id = this.viewmodel.prototype.get_model_id(
                    mp.safe_int( vm_id ) )
            if( id ) {
                return this.viewmodels({ 'ids': [ id ] })[0]
                }
            },

        get_tag: function( tag ) {
        /*
            Get first VM by EXACT TAG MATCH or return undefined
        */
            return this.viewmodels({ 'findWhere': { 'tag': tag } })[0]
            },

        get_from_slug: function( path ) {
        /*
            Get first VM by slug (should be 1 or none, but config can be bad).
            Assumes first non-underscore path is slug for item
        */
            if( path ) {
                path = path.split('/')
                while( path.slice(-1)[0][0] === mpp.NAV_NO_CONTENT ) {
                    path.pop()
                    }
                const slug = path.pop()
                if( slug ) {
                    return this.viewmodels({ 'findWhere': { 'slug': slug } })[0]
                    }
                }
            },

        })

    })();

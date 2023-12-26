/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Base Model bag - extends Backbone collection
    "Bag" used to avoid confusion with "Content Collections" (i.e., trees).

    Bags hold ALL models that were loaded from the server in different
    groupings based on content specialization/functionality.
    They are the basis for creating Viewmodel bags that represent
    filtered/sorted subsets.

    ALthough these are backbone collections, many of them do NOT use
    Backbone url to load content; most content is loaded through the
    optimized bootstrapping process.
*/
(function() { 'use strict';

    mpp.ModelBag = Backbone.Collection.extend({
        _bag_type: "ERROR - ABSTRACT BASE BAG",

        initialize: function() {
        /*
			Backbone constructor, setup event handlers for the bag
        */
            const self = this
            //mp.log_debug("CREATE", self.logname())

            // Set to true when data is first loaded
            self.fetched = false

            self.on( 'add', function( model, bag, options ) {
	                //mp.log_debug("ADD", model.logname(), " to ", self.logname())
            		})
            self.on( 'remove', function( model, bag, options ) {
	                //mp.log_debug("REMOVE", model.logname(), " from ", self.logname())
            		})
            self.on( 'change', function( model, options ) {
                    if( options.no_bubble ) return
            		//mp.log_debug("CHANGE", model.logname(), " in ", self.logname())
                    })
            },

        all_ids: function() {
            return this.pluck('id')
            },

        id_filter: function( ids ) {
        /*
            Return a JS array of models that match ids.
            The order of the returned array should match the order of ids
            provided, so any ordering requested by server is preserved.
        */
            let rv = []
            const self = this
            ids.forEach( function( id ) {
                const item = self.get( id )
                item && rv.push( item )
                })
            return rv
            },

        logname: function() {
            return this._bag_type + " bag (len:" + this.length + ") "
            },
        })

    })();

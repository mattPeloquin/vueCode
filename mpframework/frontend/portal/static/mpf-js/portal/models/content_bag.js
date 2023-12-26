/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Content base bag
    Store polymorphic content models (see content.js) for system content.

    Model bags filter themselves to create subset arrays which are
    used by ViewModels. These subset arrays hold copies of the Item
    instances from the global Items bags.
*/
(function() { 'use strict';

    mpp.ContentBag = mpp.ModelBag.extend({

        /*----------------------------------------------------
            Heterogeneous content bags

            Bags may have different types of model specializations.
            Efficient downcasting is supported by registering the Model
            with mpp.model_types using the type returned by the server.
       */

        reset: function( models, options ) {
        /*
            Override backbone reset to add downcasted items into bag
        */
           const self = this
            mp.log_debug("reset: ", self.logname(), models.length, " models")
            //mp.log_time_start("RESET " + self._bag_type )

            const downcast_models = []
            models = mp.safe_array( models )
            models.forEach( function( item ) {
                downcast_models.push( self.create_downcast_model( item ) )
                })

            const set_models = mpp.ModelBag.prototype.reset.call( self,
                                                    downcast_models, options )
            self.fetched = true

            //mp.log_time_mark("RESET " + self._bag_type)
            return set_models
            },

        add_item: function( item_data ) {
        /*
            Override backbone add to take model JSON and create downcast
        */
            const model = this.create_downcast_model( item_data )
            mpp.ModelBag.prototype.add.call( this, model )
            return model
            },

        create_downcast_model: function( item ) {
            // Don't use model_types get/set here, to allow for override of model
            const type = mpp._model_types && mpp._model_types[ item.type_db ]
            return type ? new type( item ) : new this.model( item )
            },

        })

    })();

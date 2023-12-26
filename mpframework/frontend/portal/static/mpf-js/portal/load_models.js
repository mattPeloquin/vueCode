/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Load portal models from bootstrap and user-specific data.

    The portal requires some model data to be inflated to start rendering,
    so data is sent progressively, with early data focused on browser-cacheable
    information and top-level collections.

    The following are assumed in bootstrap data for initial inflations:

        categories, groups, types, trees, items

    Other data is then merged when it arrives. Since the data may come in
    at any time, it's arrival is polled for, so the expected data groups
    from the server are hardcoded, since it isn't known what will be sent.
*/
(function() { 'use strict';

    // Track model inflation that needs to occur before KO binding
    // Setup to be extensible for platform extensions
    mpp.portal_loading = _.extend( mpp.portal_loading || {}, {
        framework_model_inflation: false,
        })
    mpp.portal_loading_done = function() {
        return Object.keys( mpp.portal_loading ).every( function( key ) {
            return mpp.portal_loading[ key ]
            })
        }

    mpp.load_models = function() {
    /*
        Inflate and merge models
    */
        // Model collections that will be filled with bootstrap data
        mpp.models = {
            types: new mpp.Types(),
            groups: new mpp.Groups(),
            categories: new mpp.Categories(),
            trees: new mpp.Trees(),
            items: new mpp.Items(),
            }

        inflate_models('types')
        inflate_models('groups')
        inflate_models('categories')
        inflate_models('items')
        inflate_models('trees')
        _models_queued = true
        }

    function inflate_models( name ) {
    /*
        Reset each set of models with bootstrap data in order
        using synchronous list, then merge.
    */
        init_data_load( name )

        when_models_loaded_inflate(
            function inflate() {
                mpp.models[ name ].reset( mp.load_data[ name ] )
                delete mp.load_data[ name ]
                },
            "inflating " + name )
        }
    const when_models_loaded_inflate = mp.run_when_ready_factory( "models_inflate",
        function() {
            // Don't start until all data is available
            return _models_queued && !!mp.load_data && mp.load_data.types !== false &&
                mp.load_data.groups !== false && mp.load_data.categories !== false &&
                mp.load_data.items !== false && mp.load_data.trees !== false
            },
        { done: function() {
            mpp.portal_loading.framework_model_inflation = true
            mp.log_highlight2("CORE MODELS LOADED")

            merge_model_data('trees_delta')
            merge_model_data('items_delta')
            if( mp.user.is_ready ) {
                merge_model_data('trees_user')
                merge_model_data('items_user')
                merge_model_data('trees_user_delta')
                merge_model_data('items_user_delta')
                }
            }
        })
    let _models_queued = false

    function init_data_load( name ) {
        // Use false as a placedholder in load_data until data is loaded
        if( typeof mp.load_data[ name ] === 'undefined' ) {
            mp.load_data[ name ] = false
            }
        }

    function merge_model_data( name ) {
    /*
        Merge data into models after inflation and data is available
    */
        init_data_load( name )

        // HACK - merge data name must start with model bag name
        const bag = name.split('_')[0]

        mp.run_when_ready(
            function() {
                return !!mp.load_data && !!mp.load_data[ name ]
                },
            function merge_models() {
                //mp.log_time_start("MERGE " + name)

                _.each( mp.load_data[ name ], function( merge_item ) {
                    // If model exists, update it
                    let model = mpp.models[ bag ].get( merge_item.id )
                    if( model ) {
                        model.set( merge_item )
                        }
                    // Create a new one if type data is present
                    else if( merge_item.type_db ) {
                        model = mpp.models[ bag ].add_item( merge_item )
                        }
                    else {
                        mp.log_debug("Merge ignored: ", merge_item)
                        }
                    // If model already in use, update values from merge
                    if( model && model.lazy_init_done ) {
                        model.lazy_init_done = false
                        model.lazy_init()
                        }
                    })

                // Garbage collect the original data, and mark merge as complete
                delete mp.load_data[ name ]
                mp.load_data[ name ] = true

                //mp.log_time_mark("MERGE " + name)
                },
            { msg: "merge " + name, no_wait: true, async: 1 })
        }

    })();

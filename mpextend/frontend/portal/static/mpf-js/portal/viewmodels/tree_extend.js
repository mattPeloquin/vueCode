/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extend Tree ViewModel additions
*/
(function() { 'use strict';

    /*
        Some tree updates can only occur after items are loaded,
        and some can be expensive for large data sets (e.g., looking
        into all tree items to calculate status), wait for items
        and delay to avoid holding back initial rendering.
    */
    mpp.when_items_fetched = mp.run_when_ready_factory( "items_fetched",
        function() {
            return mpp.models.items && !!mpp.models.items.fetched
            },
        { no_wait: false, async: 400 })

    /*--------------------------------------------------------------
        Tree ViewModel Bag extensions
    */
    const _tree_vms_init = mpp.TreeVMs.init

    mpp.TreeVMs.init = function( self, models ) {
        _tree_vms_init( self, models )

        // Plan groupings
        self.accessor_ko( 'tops_plan_in', function() {
                return self.viewmodels({ tops: true, filter_groups: ['plan_in'] })
                })
        self.accessor_ko( 'tops_plan_out', function() {
                return self.viewmodels({ tops: true, filter_groups: ['plan_out'] })
                })

        // Status groupings
        self.accessor_ko( 'tops_in_progress', function() {
                return self.vm_attr({ status: ['S'] }, { tops: true })
                })
        self.accessor_ko( 'tops_remaining', function() {
                return self.vm_attr({ status: [''] }, { tops: true })
                })
        self.accessor_ko( 'tops_completed', function() {
                return self.vm_attr({ status: ['C', 'A'] }, { tops: true })
                })

        }

    /*--------------------------------------------------------------
        Tree ViewModel
    */
    const _TreeVM_init = mpp.TreeVM.init

    mpp.TreeVM.init = function( self, model ) {
        _TreeVM_init( self, model )

        /*
            To support dynamic progress tracking in root/top-collections,
            status of all items in the tree need to monitored.
        */
        self.completed_percent = false
        if( self.is_top ) {

            // Make percent complete for root an observable that is
            // refreshed by doing completion bags on updates
            self.completed_percent = ko.observable()
            self.update_status = _.debounce(
                function() {
                    _status_arrays()
                    self.completed_percent( self._completed_percent() )
                    },
                mp.options.refresh_debounce_delay )

            // Make sure items are present on client
            mpp.when_items_fetched( function tree_status() {
                // Do initial status if this collection has been started
                self.model.get('status') && self.update_status()

                // Listen for status changes to any items in this tree
                const models = mpp.models.items.id_filter( self.model.all_items() )
                models.forEach( function( model ) {
                    self.listenTo( model, 'change:status',
                        function( model, options ) {
                            self.update_status()
                            })
                    })
                })
            }

        // Progress for children
        self.accessor_ko( 'all_in_progress', function() {
            return mpp.vm_items().vm_attr(
                    { status: ['S'] }, { ids: model.all_items() } )
            })
        self.accessor_ko( 'all_remaining', function() {
            return mpp.vm_items().vm_attr(
                    { status: [''] }, { ids: model.all_required() } )
            })
        self.accessor_ko( 'all_completed', function() {
            return mpp.vm_items().vm_attr(
                    { status: ['C', 'A'] }, { ids: model.all_items() } )
            })
        self.accessor( 'all_models_to_complete', function() {
            return mpp.vm_items().models({ 'ids': model.all_to_complete() })
            })
        function _status_arrays() {
            // Rebuild these arrays based on current item status
            self.accessor( 'all_models_to_complete_started', function() {
                    return mpp.vm_items().models_attr(
                            { status: ['S'] }, { ids: model.all_to_complete() } )
                    })
            self.accessor( 'all_models_to_complete_completed', function() {
                    return mpp.vm_items().models_attr(
                            { status: ['C', 'A'] }, { ids: model.all_to_complete() } )
                    })
            }
        _status_arrays()

        // Date/time for children
        const date_options = {
            ids: model.items_core(),
            sort: true,
            sort_attr: 'available',
            }
        const upcoming = _.extend( { filter_groups: ['upcoming'] }, date_options )
        self.accessor( 'items_upcoming', function() {
            return mpp.vm_items().viewmodels( upcoming )
            })
        date_options.sort = 'desc'
        const previous = _.extend( { filter_groups: ['previous'] }, date_options )
        self.accessor( 'items_previous', function() {
            return mpp.vm_items().viewmodels( previous )
            })

        }

    _.extend( mpp.TreeVM.prototype, {

        navigate_init: function( panel ) {
        /*
            Play selected item upon navigation if NOT in iframe.
        */
            const start_item = $( panel ).find(".mpp_action_select_item")
            if( start_item.length ) {
                start_item.removeClass('mpp_action_select_item')
                mpp.auto_play = false
                if( !mp.is_iframe ) {
                    this.next_core().user_access_action( this )
                    }
                }
            },

        completed: function() {
        /*
            Trees are completed when all items are completed, or all required
            items are completed.
            Once marked completed they never go back, even if items change
        */
            let rv = this.model.get('status') === 'C'
            if( !rv && this.all_models_to_complete().length ) {
                // Set the TREE to complete if everything in it is done
                rv = this.all_models_to_complete().length ===
                        this.all_models_to_complete_completed().length
                if( rv ) {
                    this.model.set( 'status', 'C' )
                    this.model.update( true )
                    }
                }
            return rv
            },

        _completed_percent: function() {
        /*
            Calculate percent complete based on contents of node or prior completion
        */
            let rv = this.completed() ? 100.0 : 0.0
            if( !rv ) {
                function _item_points( memo, item ) {
                    return memo + item.get('points')
                    }
                const points_to_complete = _.reduce( this.all_models_to_complete(),
                                                   _item_points, 0 )
                if( points_to_complete > 0 ) {
                    // Calculate percentage taking into account option for credit for starting
                    let completed_points = _.reduce( this.all_models_to_complete_completed(),
                                                     _item_points, 0 )
                    if( !this.sb_option('portal.no_half_complete_if_started') ) {
                        const started_points = _.reduce( this.all_models_to_complete_started(),
                                                       _item_points, 0 )
                        completed_points += ( started_points / 2 )
                        }
                    rv = Math.round( 100 * ( completed_points / points_to_complete ))
                    }
                }
            return rv
            },

        })

    })();


/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Customization and additions for Plans
*/
(function() { 'use strict';

    mpp.get_plan = function( plan_id ) {
        // Get the default or requested plan
        return mpp.models.plans &&
                    mpp.models.plans.get( plan_id ? plan_id : mpp.plan_default )
        }

    mpp.init_plans = function() {
        // Only relevant for authenticated users
        mp.user.is_ready && _inflate_models()
        }

    // Only register portal loading events based on authentication
    mpp.portal_loading = _.extend( mpp.portal_loading || {}, {
        plan_model_inflation: !mp.user.is_ready,
        })

    function _inflate_models() {
        mp.load_data.plans === undefined && ( mp.load_data.plans = false )
        mpp.models.plans = new mpp.Plans()

        // Load data from models once API bootstrap call completes
        mp.run_when_ready(
            function() {
                return !!mp.load_data && mp.load_data.plans !== false
                },
            function plan_data() {

                mpp.models.plans.reset( mp.load_data.plans )
                delete mp.load_data.plans

                // One plan at a time can be default for the portal
                // FUTURE - for now just take first if exists,
                // change when multiple plans are implemented
                mpp.plan_default = mpp.models.plans.length ?
                            mpp.models.plans.models[0].id : 0

                mpp.portal_loading.plan_model_inflation = true
                })
        }

    // Attach add/remove logic in the binding handler
    ko.bind_extend.bind_nav_content.init.push(
        function plan_init( element, value ) {
            if( !( mp.user.is_ready && $( element ).parents(".es_plan").length ) ) {
                return
                }
            const tree = mpp.get_model( element )
            // Card button to add/remove from plan
            const add_remove =
                '<div class="es_card_controls">' +
                    '<div title="Add/Remove" class="es_plan_button es_theme_overlay ' +
                        'fa es_button_flat">' +
                    '</div></div>'
            $( element ).prepend( add_remove )
            const plan_button = $( element ).find(".es_plan_button")
            if( tree.in_plan() ) {
                plan_button.addClass('fa-minus')
                }
            else {
                plan_button.addClass('fa-plus')
                }
            // Handle the add and remove
            plan_button.click( function() {
                if( tree.in_plan() ) {
                    tree.plan_remove( mpp.plan_default )
                    }
                else {
                    tree.plan_add( mpp.plan_default )
                    }
                })
            })

    })();

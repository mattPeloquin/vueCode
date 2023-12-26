/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Portal startup code
*/
(function() { 'use strict';

    mpp.init_portal = function() {
    /*
        Portal start is expensive, so is broken into several sections
        to keep more responsive as per Lighthouse guidelines.
    */
        mp.log_time_start("PORTAL_INIT")

        mpp.load_models()

        mp.when_ui_loaded( function portal_init() {
            mp.log_info2("Initializing portal")

            mpp.init_navigation()

            // Bring visible element for current item into view on resizes
            $( document ).on( 'layout_resize', function( _event, container ) {
                _view_active_item( container )
                })

            // Use KO to link viewmodels to DOM when portal is ready
            // Start portal binding once models loaded and UI infrastructure
            // is in place - also support an optional wait flag
            mp.run_when_ready(
                function() {
                    return mpp.portal_loading_done() && !mpp.vm_binding_wait
                    },
                function portal_bind() {
                    mpp.ko_apply_bindings()
                    _init_control()
                    mpp._portal_bound = true
                    },
                { no_wait: true })
            // Do initial navigation
            mp.run_when_ready(
                function() { return mpp._portal_bound },
                function portal_start() {

                    // Go to the right place for this load
                    mp.show_wait_overlay( false )
                    mpp.navigate_start_point()
                    $(".mp_hide_portal").removeClass('mp_hide_portal')

                    // Run any scripting that needs values loaded from server
                    mpp.portal_page_script()

                    mp.layout_resize()
                    mpp._portal_ready = true
                    mp.log_highlight("PORTAL READY")
                    mp.log_time_mark("PORTAL_INIT")
                    })
            })
        }

    mpp.init_controls = function( element ) {
        // Slider will initialize with left button click
        $( element ).find(".es_slider_left").click()
        }

    function _view_active_item( container ) {
    /*
        If an active item is set for the portal, scroll it into view if
        if is visible in the current pane
    */
        container = container || document
        const item = ko.unwrap( mpp.vm_current.item )
        if( item.id ) {
            item.jQuery( container ).each( function() {
                if( $(this).is(":visible") ) {
                    this.scrollIntoView({ block: 'center' })
                    return false
                    }
                })
            }
        }

    function _init_control() {
    /*
        Add dynamic listeners for controls, since they are created when
        parts of the UI are rendered.
    */
        // Tooltip support
        $( document )
            .on( 'mouseenter touchenter pointerenter focusin',
                    ".mpp_tool_popup", function() {
                $(this).find(".es_content_tool_popup").first().removeClass('mp_hidden')
                })
            .on( 'mouseleave touchleave pointerleave focusout',
                    ".mpp_tool_popup", function() {
                $(this).find(".es_content_tool_popup").first().addClass('mp_hidden')
                })

        // Left/right slide for horizontal items
        $( document )
            .on( 'resize', ".es_items_horizontal", function() {
                _slide_setup( $( this ).find(".es_items_container"), false )
                })
            .on( 'click', ".es_slider_left", function() {
                _slide_move( this, false )
                })
            .on( 'click', ".es_slider_right", function() {
                _slide_move( this, true )
                })
        }

    function _slide_move( control, right ) {
    /*
        Assumes control is direct descendent of parent with overflow hidden,
        will adjust the sliding window displayed in parent.
    */
        const outside = $( control ).parents(".es_items_horizontal")
        const container = outside.find(".es_items_container")
        const outside_width = outside.width()
        const width = container.width()
        let pos = container.data('pos') || 0
        if( width < outside_width ) {
            return
            }
        pos = pos + ( (right ? -1 : 1) * outside_width )
        pos = Math.min( 0, pos )
        pos = Math.max( pos, outside_width - width )
        container.css( 'transform', 'translateX(' + pos + 'px)' )
        container.data( 'pos', pos )
        _slide_setup( container )
        }
    function _slide_setup( container ) {
    /*
        Assumes control is direct descendent of parent with overflow hidden,
        will adjust the sliding window displayed in parent.
    */
        container = $( container )
        const pos = container.data('pos') || 0
        const outside = $( container ).parents(".es_items_horizontal")
        outside.find(".es_slider_left").toggleClass( 'mp_hidden', pos >= 0 )
        outside.find(".es_slider_right").toggleClass( 'mp_hidden',
                    container.width() <= outside.width() - pos )
        }

    })();

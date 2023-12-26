/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Staff-specific UI initialization
*/
(function() { 'use strict';

    mp.init_admin_style = function() {

        // Add any CSS mappings to admin headers
        const cols = $(".mp_admin_table thead th")
        _.each( mp.admin_cl_header_css, function( classes, header ) {
            cols.filter( ".column-" + header ).addClass( classes )
            })

        // Changelist field CSS fixups
        const row_items = $(".mp_row > th, .mp_row > td")
        row_items.has("img").css('text-align', 'center').css('width', '4em')
        row_items.has("input[type=checkbox]").css('text-align', 'center').css('width', '2em')
        _.each( mp.admin_cl_field_css, function( classes, field ) {
            row_items.filter( ".field-" + field ).addClass( classes )
            })

        // Items loaded per-screen
        mp.init_admin_style_select && mp.init_admin_style_select()

        }

    mp.init_admin_layout = function() {

        // Items loaded per-screen
        mp.init_admin_layout_select && mp.init_admin_layout_select()

        }

    mp.init_admin_events = function() {

        mp.viz_add_toggle( document, { no_icon: true } )

        // Implement collapsible admin sections
        $( document ).on( 'click', '.mp_collapse_handler', function() {
            const title = $(this)
            if( !title ) return
            const fieldset = title.parents(".mp_collapse")
            if( !fieldset ) return

            // Click always transforms current state
            // A session with no app state starts with default layout in admin code
            // Otherwise session state is added at startup
            fieldset.toggleClass('mp_closed')

            // Store current collapsable fieldset state in preferences
            // Make a selector to use to find the title on reload
            const html = title.html()
            let selector = title.mpselector(['mp_closed'])
            if( !(html && selector) ) return
            selector = selector + ':contains("' + html + '")'
            let class_toggle = []
            class_toggle.push({ closest: '.mp_collapse',
                        class: 'mp_closed',
                        on: fieldset.hasClass('mp_closed') })
            mp.preference_store( selector, 'class_closest', class_toggle, 'staff' )

            // Opening and closing sections change height, so manage layout
            mp.layout_resize()
            })

        }

    })();

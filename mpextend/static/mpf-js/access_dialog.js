/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    PA access dialog and coupon support

    Because of shared logic, coupon and access dialog are tied together.
    They are mostly used in the portal, but are independent of it,
    populating information through the PA API, so with appropriate
    CSS context can be used in other pages.
*/
(function() { 'use strict';

    mp.access_coupon = function( coupon_code, possible_pa_array ) {
    /*
        Apply PA-specific coupon
        Support executing a request against a PA with just a coupon code;
        if coupon is valid for a specific PA, the request will be sumbitted
    */
        mp.log_info("access_coupon: ", coupon_code)
        _close_active()
        function coupon_response( info ) {
            return _apply_coupon_info( possible_pa_array, info )
            }
        mp.fetch({
            url: mpurl.api_coupon_info + coupon_code,
            finished: coupon_response,
            })
        }

    /*--------------------------------------------------------------
        Access dialog

        Logic for managing access to content items. The nominal
        case is to display an option dialog, but in some scenarios the
        user may not see the dialog because an option is automatically
        selected or when visitors are redirected to sign in.
        This allows code sharing for the various permutations.
    */
    mp.access_dialog = function( pas, accounts ) {
        mp.log_debug("access_dialog: ", pas, " -> ", accounts)
        _close_active()

        // Create array of all pas
        const pa_array = []
        let all_free = true
        let any_free = false
        for( var key in pas ) {
            const pa = pas[ key ]
            pa_array.push( pa )
            all_free = ( all_free && pa.access_free )
            any_free = ( any_free || pa.access_free )
            }

        // Setup array of accounts
        const account_array = []
        if( accounts ) {
            for( var key in accounts ) {
                account_array.push( accounts[ key ] )
                }
            _.sortBy( account_array, 'order' )
            }

        // Determine options and render into dialog form
        _render_dialog( pa_array, { accounts: account_array } )
        _active_open()
        }

    // Use singleton since only one access dialog displayed at a time
    // Store html and dialog instance for use in setup and teardown
    let _active_open = null
    let _active_template = null
    let _active_instance = null

    function _close_active() {
        // Close dialog if open
        _active_instance && _active_instance.close()
        _active_instance = null
        }

    function _submit_new_license( pa_id, event ) {
    /*
        PA submits flow through here; the dialog may or may not be
        be visible to the user when submitted, but should be rendered.
    */
        if( mp.user.is_ready ) {
            mp.log_info("submit access request: ", pa_id)
            if( !_active_instance ) {
                _active_open()
                }
            // Use the pa button on the dialog to submit
            _active_instance.find("#access_pa_id").change_val( pa_id )
            _active_instance.find("#access_select_form").submit()
            }
        else {
            mp.log_info("Redirect visitor to login for: ", pa_id)
            mp.access_login( pa_id,
                    _active_instance.find("#coupon_code").val() )
            }

        // Ensure that downstream processing won't interfere with actions
        event && event.preventDefault()
        }

    function _pa_buttons_html( pa_array ) {
        // Display the PAs from least expensive to most
        let rv = ""
        const pa_button_template = _.template(
                    $("#template_access_pa_button").html() )
        _.each( _.sortBy( pa_array, 'price' ), function( pa, index ) {
            pa['location'] = window.document.location.pathname
            pa['index'] = index
            rv += pa_button_template( pa )
            })
        return rv
        }

    function _render_dialog( pa_array, options ) {
    /*
        Setup access dialog by pulling template pieces together into
        dialog HTML, and then modify DOM elements in dialog after open
    */
        options = options || {}
        // Assume failure
        let title = mp.sbt('access_title_problem')
        let login = ""
        let pa_buttons = mpt.ITEM_NOT_CONFIGURED
        let accounts = ''
        const account_array = options.accounts

        // Setup default main html (PA buttons)
        const button_html = _pa_buttons_html( pa_array )
        if( button_html ) {
            pa_buttons = button_html
            if( options.notify ) {
                title = mp.sbt('access_title_notify')
                }
            else {
                accounts = _account_select_html( account_array )
                title = ( pa_array.length > 1 ) ?
                            mp.sbt('access_title_select') :
                            mp.sbt('access_title_confirm')
                if( !mp.user.is_authenticated ) {
                    login = mp.sbt('access_login')
                    }
                }
            }

        // Render the template to HTML, then add to DOM so the
        // new HTML can be manipulated in DOM before displayed
        const html = _.template( $("#template_access_select").html() )({
                accounts: accounts,
                pa_buttons: pa_buttons,
                login: login,
                title: title,
                coupon_prompt: mp.sbt('coupon_prompt'),
                coupon_apply: mp.sbt('coupon_apply'),
                access_location: mp.sbt('access_location'),
                access_account_apply: mp.sbt('access_account_apply'),
                })
        const tag = 'access_' + mp.rand_str()
        $("mptools").append('<div id="' + tag + '" class="mp_hidden"></div>')
        const new_template = $("mptools").find( "#" + tag )
        new_template.append( html )
        _active_template = new_template

        // Fixups that have to occur after dialog is opened
        function after_open( dialog ) {
            _active_instance = dialog
            _add_behavior()
            _account_behavior( account_array )
            _toggle_option_visibility( account_array, pa_array, options )
            mp.set_country_selector( _active_instance.find("#access_country") )
            }

        // Setup the function to be called if dialog to be opened
        _active_open = function() {
            // Get html for template from DOM and remove
            const template_html = new_template.html()
            _active_template.remove()
            // Open the dialog
            mp.dialog_html( template_html, {
                                after_open: after_open,
                                })
            }
        }

    function _toggle_option_visibility( accounts, pas, options ) {
        options = options || {}

        _active_instance.find("#access_coupon").toggleClass( 'mp_hidden',
                    !pas || pas.length < 1 || !!options.notify )

        // Show account option if more than one
        _active_instance.find("#access_account").toggleClass( 'mp_hidden',
                    !accounts || accounts.length < 2 || !!options.notify )

        // Show tax location if SELECTED account doesn't have location
        const account = _selected_account( accounts )
        _active_instance.find("#access_location").toggleClass( 'mp_hidden',
                    !account || !account.admin || !!options.notify ||
                    !!(account.postal_code && account.country) )
        }

    //-------------------------------------------------------------------------

    function _add_behavior() {
    /*
        Handle requests to select a PA and/or apply coupon code

        The request for PA access happens with form submit. If a coupon value
        is in the dialog when submitted, the backend will try to apply it.

        If the coupon field is empty when a PA button is pressed, the PA
        is just submitted. If there is a coupon typed in when a PA button is
        pressed, or coupon Apply/Enter if pressed, an ajax call is made
        to the server before submission to check if coupon is valid.

        If the coupon is general, it will be applied against the PA that
        was selected, or user will be prompted to press a PA button.

        If coupon is specific to a PA, the submission will use that PA.
        This allows submission of PAs that aren't displayed on the dialog, and
        makes the use case of someone using a targeted coupon not getting
        messed up by the wrong PA button.

        Returns false if propagation of event should be stopped (no form submission)
    */
        function process_request( pa_id, event ) {

            // If coupon code present, use coupon processing path
            const coupon_code = _active_instance.find("#coupon_code").val()
            if( coupon_code ) {
                function coupon_response( info ) {
                    return _apply_coupon_info( [ pa_id ], info )
                    }
                mp.fetch({
                    url: mpurl.api_coupon_info + coupon_code,
                    data: { 'pa_id': pa_id },
                    finished: coupon_response
                    })
                return false
                }

            // If PA button pressed with no coupon, just submit it
            if( pa_id ) {
                _submit_new_license( pa_id, event )
                return
                }
            // Otherwise assume coupon request with no coupon code
            mp.dialog_open( mp.sbt('coupon_code') )
            return false
            }

        // PA button events
        _active_instance.find(".access_pa_button")
             // Selection of a PA button
            .on( 'click', function( event ) {
                    // Allow embedded links to process events
                    if( !( event.target instanceof HTMLAnchorElement) ) {
                        if( !mp.access_free_all ) {
                            return process_request( $(this).data('pa_id'), event )
                            }
                        }
                    })
             // Keyboard support
             // Turn return into click and arrow keys into focus movement
            .keydown( function( event ) {
                if(_.includes( [13], event.keyCode )) {
                    event.preventDefault()
                    $(this).click()
                    }
                else if(_.includes( [39, 40], event.keyCode )) {
                    $(this).parent().next().find(".access_pa_button").focus()
                    }
                else if(_.includes( [37, 38], event.keyCode )) {
                    $(this).parent().prev().find(".access_pa_button").focus()
                    }
                })

        // When apply coupon button is pressed, try general processing for the coupon
        _active_instance.find("#coupon_apply").click( function() {
                return process_request()
                })
        _active_instance.find("#coupon_code").keypress( function( event ) {
                if( event.keyCode == 13 ) {
                    return process_request()
                    }
                })
        }

    function _apply_coupon_info( pas, info ) {
    /*
        Handle coupon paths that are not submitting access form
        Apply coupon feedback from server by either submitting a request
        or opening a new access dialog based on the coupon
    */
        try {
            info = mp.unpack_nested_json( info )
            const coupon = info.coupon
            if( !coupon ) {
                mp.dialog_open( mp.sbt('coupon_invalid').replace(
                                    '%code%', info.original.code ) )
                }
            else {
                if( coupon.available ) {
                    // If coupon has specific PA, use it and ignore previous selected
                    // if coupon is generic, use original PA if available
                    const pa_id = coupon.pa ? coupon.pa : info.original.pa_id
                    pas = pa_id ? [ _.find( pas, ['id', pa_id] ) ] : pas

                    // If dialog not already open, render access form to show PAs
                    // and whether this is confirmation or just notification
                    if( !_active_template ) {
                        _render_dialog( pas, { notify: !!pa_id } )
                        }

                    // Ensure form has coupon code (e.g., called from access_coupon)
                    $( _active_template ).find("#coupon_code")
                            .change_val( coupon.code )

                    if( pa_id ) {
                        _submit_new_license( pa_id )
                        }
                    else {
                        // If dialog is already open, message about selecting a PA
                        // otherwise open dialog up for first time
                        if( _active_instance ) {
                            mp.dialog_open( mp.sbt('access_coupon').replace(
                                        '%code%', coupon.code ) )
                            }
                        else {
                            _active_open()
                            }
                        }
                    }
                else {
                    mp.dialog_open( mp.sbt('coupon_expired').replace(
                                '%code%', coupon.code ) )
                    }
                }
            }
        catch( e ) {
            mp.log_error("Exception applying coupon: ", e)
            }
        // Make sure the template was cleaned up if _active_open wasn't called
        _active_template.remove()
        }

    //-------------------------------------------------------------------------

    function _account_behavior( account_array ) {
        // Support no account so staff can look at options (but wont' be able to buy)
        if( !account_array || !account_array.length ) return

        // Whenever account is changed, update location
        _active_instance.find("#account_select").change( function() {
                const account = _selected_account( account_array )
                _active_instance.find("#access_postal_code")
                        .change_val( account.postal_code )
                _active_instance.find("#access_country")
                        .change_val( account.country )
                _toggle_option_visibility( account_array )
                })

        // Add the primary (first) account's location info
        _active_instance.find("#account_select").change_val( account_array[0].id )
        }

    function _selected_account( account_array ) {
        const id_match = { 'id': mp.safe_int(
                _active_instance.find("#account_select").val() ) }
        return _.find( account_array, function( account ) {
                    if( _.matches( id_match )( account ) ) {
                        return account
                        }
                    })
        }

    function _account_select_html( account_array ) {
        let rv = ""
        _.each( account_array, function( account ) {
            rv += '<option value="' + account.id + '">' + account.name + '</option>'
            })
        return rv
        }

    })();

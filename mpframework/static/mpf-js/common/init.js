/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Initialization code run on every page
*/
(function() { 'use strict';

    mp.local_ui = mp.local_get('ui')

    mp.init_ui = function( start_ready, end_ready ) {
    /*
        Call the remainder of UI initialization once document is ready,
        which should be after all scripts and global vars are loaded.
    */
        // If designated as a closable popup, try to do so
        // This will only succeed if window is open in script, and is used
        // for popup login scenarios where the session cookie should now
        // be added to the URL in the browser
        if( mp.is_popup_close ) {
            window.close()
            }

        // Release hold on jquery ready
        $.holdReady( false )

        // When DOM is ready, complete the setup
        $( document ).ready( function() {
            mp.log_highlight("DOM READY")

            // Inoculate against things like browser origin security changing,
            // so errors in these various script-driven style things won't
            // prevent the portal from showing at all
            try {
                mp.show_wait_init()
                start_ready && start_ready()
                event_init()
                disable_browser_ui()
                mp.ui_state_init()
                mp.style_init()
                mp.layout_init()
                mp.idle_init()
                mp.init_menus( ".mp_menu_staff, .mp_menu_admin", 'mp_menu_highlight' )
                mp.init_menus( ".mp_menu_user", 'es_menu_highlight' )
                mp.init_tooltips()
                mp.init_clipboard()

                // Set preferences for items that will already be available
                mp.preferences_init('site')
                mp.preferences_init('staff')

                end_ready && end_ready()
                }
            catch( e ) {
                mp.log_error("Init UI exception: ", e)
                }

            // Show the UI
            $(".mp_hide_load").removeClass('mp_hide_load')
            $("#mp_loading").addClass('mp_hidden')
            user_init()
            mp.layout_resize()

            // Allow items waiting on UI loading to run
            mp._loaded_ui = true
            mp.log_highlight("UI LOADED")
            })
        }

    mp.user_logout = function() {
    /*
        Reset/cleanup on explicit logout
    */
        mp.local_remove('ui')
        mp.local_remove('nav')
        mp.local_remove('preferences_viz')
        mp.local_remove('preferences_site')
        mp.local_remove('preferences_staff')
        local_update = false
        }
    let local_update = true

    function user_page_unload() {
        if( local_update ) {
            mp.local_update( 'ui', mp.local_ui )
            mp.local_update( 'nav', mp.local_nav )
            }
        }

    function event_init() {
    /*
        Register special event handling by class
    */
        mp.is_page_admin && mp.init_admin_events()

        // Setup staff help toggle using preference state of switch
        $( document ).on( 'click', '.mp_help_staff_toggle', function() {
            $(".mp_help_staff_toggle").toggleClass('mp_off')
            const off = mp.help_off()
            $( mp.HELP_STAFF_SELECTOR ).toggleClass( 'mp_hidden', off )
            mp.preference_store( '.mp_help_staff_toggle', 'class', [{
                class: 'mp_off',
                on: off,
                }])
            })

        // Show selected filename, sans path when file uploads selected
        $( document ).on( 'change', '.mp_file_control input', function() {
            const name = this.value.replace( /.*[\/\\]/, '' )
            $(this).closest(".mp_upload").find(".mp_file_name").html( name )
            })

        // Setup unload handler
        $( window ).on( 'beforeunload', function beforeunload() {
            if( mp.inline_download ) {
                mp.inline_download = false
                }
            else {
                mp.show_wait_overlay( true )
                user_page_unload()
                }
            })
        }

    function disable_browser_ui() {

        // Suppress browser right-click menu for users
        if( !mp.user.access_staff ) {
	        $( window ).bind( 'contextmenu', function(e) {
                e.preventDefault()
                })
            }

        // Disable some selection
        // Want to prevent spurious selection of application elements, but still allow
        // mouse/touch manipulation of text in content areas for user
        $(".mp_menu, .mpp_control").addClass('mp_select_off')
        if( !mp.user.access_staff ) {
            $("body").addClass('mp_select_off')
            if( !mp.options.no_text_selection ) {
                $(".mp_main").addClass('mp_select_text')
                }
            }

        if( mp.is_iframe ) {
            $("body").addClass('mp_iframe')
            // Support hiding some UI in an iframe
            $(".mp_no_iframe").addClass('mp_hidden')
            }
        }

    function user_init() {
    /*
        Initialize user-specific items
    */
        $(".mp_user_name").html( mp.user.name )

        // Set image width to 0 if no src to maintain vertical
        if( mp.user.image ) {
            $(".mp_user_image").attr("src", mp.user.image )
            $(".mp_user_icon").hide()
        } else {
            $(".mp_user_image").css("width", 0).css("height", 0)
            }

        // Fixup account menu links to load page for current account
        if( mp.user.ga_admin ) {
            $(".mp_ga_menu_root").removeClass('mp_hidden')
            const ga = mp.local_nav.ga_last
            if( ga ) {
                $("mp_ga_menu").find("a").each( function() {
                    if( _.endsWith( this.href, '_' ) ) {
                        this.href = this.href.replace( '/_', '/' + ga )
                        }
                    })
                }
            }
        }

    })();

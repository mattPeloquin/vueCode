/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Javascript Layout fixups
*/
(function() { 'use strict';

    mp.layout_init = function() {
    /*
        Called once at startup to setup layout handling
    */
        init_layout_widgets()
        mp.is_page_admin && mp.init_admin_layout()

        // Setup top bar early to push any elements down immediately
        layout_top_bar()

        // Setup resizing events
        $( window ).on( 'resize orientationchange', mp.layout_resize )
        }

    /*
        Main screen resize event handling
        Adjust items in layout that can't effectively be handled via CSS.
        Try to keep the amount of script layout to a minimum.
        Floor calculated values to avoid dancing due to rounding errors.
    */
    let _current_resizer = null
    mp.layout_resize = function() {
        var container = _current_resizer()
        $( document ).trigger( 'layout_resize', container )
        }
    mp.layout_resize_set = function( resizer ) {
        // Default resize can be overridden by viewer
        resizer = resizer || mp.layout_resize_main
        _current_resizer = _.debounce( resizer,
                    mp.options.refresh_debounce_delay, { leading: true } )
        }
    mp.layout_resize_main = function() {
        layout_top_bar()
        mp.fixup_responsive_css()
        fixup_viz_css()
        const bottom_height = $(".mp_bottom").outerHeight()
        const min_height =  $( window ).height() - _top_height - bottom_height
        const main_css_adjust = {
            // Use padding so background color doesn't seep through when changing
            'padding-top': Math.floor( _top_height ) + 'px',
            'padding-bottom': Math.floor( bottom_height ) + 'px',
            'min-height': Math.floor( min_height ) + 'px',
            }
        const main_panel = $(".mp_main")
        main_panel.css( main_css_adjust )
        mp.log_debug_level > 1 && mp.log_debug("Set main CSS:", main_css_adjust)
        return main_panel[0]
        }
    mp.layout_resize_set()

    mp.layout_is_horizontal = function() {
    /*
        Returns true if horizontal/landscape layout is being used based
        on the width available to the screen.
    */
        const viewframe = $( window )
        return viewframe.width() > viewframe.height()
        }

    mp.fixup_responsive_css = function() {
    /*
        Add CSS classes based on current body size
    */
        const body = $("body")

        body.toggleClass( 'es_width_small',
                body.width() < mp.request.breakpoints.width.small )
        body.toggleClass( 'es_width_medium',
                body.width() >= mp.request.breakpoints.width.small &&
                body.width() <= mp.request.breakpoints.width.medium )
        body.toggleClass( 'es_width_large',
                body.width() > mp.request.breakpoints.width.medium &&
                body.width() <= mp.request.breakpoints.width.large )
        body.toggleClass( 'es_width_xlarge',
                body.width() > mp.request.breakpoints.width.large )

        body.toggleClass( 'es_height_small',
                body.height() < mp.request.breakpoints.height.small )
        body.toggleClass( 'es_height_medium',
                body.height() >= mp.request.breakpoints.height.small &&
                body.height() <= mp.request.breakpoints.height.medium )
        body.toggleClass( 'es_height_large',
                body.height() > mp.request.breakpoints.height.medium )

        body.toggleClass( 'es_horizontal', mp.layout_is_horizontal() )
        body.toggleClass( 'es_vertical', !mp.layout_is_horizontal() )
        }

    function layout_top_bar( screen ) {
    /*
        Setup top-bar heights and positions
        Read the height from HTML elements, and then modify as needed.
        Note that due to layout timing, need to look at the height of elements
        inside the top bar and add up vs. relying on browser top bar height.
        Bars are assumed to use absolute or fixed screen positioning and
        has no margin to the left.
        Cache value after layout for use in calcs before next layout.
    */
        screen = screen ? $( screen ) : $("body")

        // Handle any banner first, which is always at very top
        let top_height = bars_height( 0, screen, ".mp_top_banner" )

        // Next handle the different levels of bars in order they are stacked
        top_height = bars_height( top_height, screen, ".mp_staff_bar" )
        top_height = bars_height( top_height, screen, ".mp_top_bar" )

        _top_height = top_height
        }
    let _top_height = 0

    function bars_height( current_top, screen, bar_name ) {
    /*
        If the given element is a fixed position bar, place it's top at the
        old height and return the new total top height.
    */
        screen.find( bar_name ).each( function() {
            const bar = $(this)
            if( bar.css('display') != 'none') {
                bar.css({ 'top': current_top + 'px' })
                current_top += bar.outerHeight()
                }
            })
        return current_top
        }

    function init_layout_widgets( element ) {
    /*
        Setup widget and tool handlers related to layout
    */
        element = element || window.document.body

        $( element )
            // mpr_collapse responsive expanding/collapsing
            .on( 'click', ".mpr_collapse_toggle", function( event ) {
                event.stopPropagation()
                // Container can be the same as toggle
                const container = $(this).parents(".mpr_collapse")
                        .addBack(".mpr_collapse")
                const target = $( "#" + $( container ).data("collapse") )
                // Current state based on presence of show on target
                const current_show = target.hasClass('mpr_collapse_show')
                // Provide open state for overall menu
                container.toggleClass( 'mpr_collapse_open', !current_show )
                // Toggle target open/hide state
                target.toggleClass('mpr_collapse_show')
                target.toggleClass( 'mpr_collapse_hide', current_show )
                // Do a non-debounced layout resize
                mp.layout_resize_main()
                })
            .on( 'click', ".mpr_collapse_show:not(.mpr_collapse_inline)", function() {
                const element = this;
                setTimeout( function() {
                    const container = $(element).parents(".mpr_collapse")
                    container.find(".mpr_collapse_toggle")
                                .addBack(".mpr_collapse_toggle").click()
                    })
                })
        }

    function fixup_viz_css() {
    /*
        Handle dynamic sizing relating to portal visuals.
        These styles are NOT applied to protected content.
    */
        // Optimally scale and center background images
        $(".mp_image").each( function() {
            const container = $(this)
            const image = background_image( container )
            // Adjust image container height
            hero_adj( container.closest(".es_hero_container"), image )
            // Optimize image size and placement
            const scale = center_fixed_image( this, image )
            if( scale ) {
                container
                    .css( 'background-size', scale.size )
                    .css( 'background-position', scale.position )
                }
            })
        // Set height on display video
        $(".mp_video").each( function() {
            $(this).closest(".es_hero_container").each( function () {
                const container = $(this)
                const video = container.find("video")[0]
                function _vid_height() {
                    hero_adj( container, video )
                    }
                if( video.videoHeight ) {
                    _vid_height()
                    }
                else {
                    video.addEventListener( 'onloadstart', _vid_height )
                    }
                })
            })
        }

    function background_image( container ) {
    /*
        Load background image of element into new element for access.
        Caches value and returns empty if loading is not complete.
    */
        const src = container.css('background-image').replace( url_regex, '$1' )
        if( !images[ src ] ) {
            const image = new Image()
            image.onload = function image_loaded() {
                images[ this.src ] = this
                mp.layout_resize()
                }
            image.src = src
            }
        return images[ src ]
        }
    let images = {}
    const url_regex = /url\(['"]*(.*?)['"]*\)/gi

    function hero_adj( container, viz ) {
    /*
        Modify hero container based on visual width.
        Options are provided in data-hero_style or sb_options:
          (t)ext is default, height follows container
          (a)spect height follows aspect ratio of content
          (m)ax:height is aspect up to height (100px, 20em, etc)
          (f)old scales to fill above the fold
          (b)ack fills fold in background
          (backfold) fills fold in background
          (c)ss uses given height css
    */
        if( !( container.width() && viz ) ) {
            return
            }
        const win_height = $( window ).height()
        const portal_height = win_height - _top_height
        const vh_portal = Math.ceil( 100 * portal_height / win_height )
        // Get the height option from data or current theme defaults
        let option = container.data('hero_style')
        option = option || mpp.sb_option( 'portal.hero_style', container )
        option = option.toLowerCase()
        // Setting height to whatever is in box is default
        let height = option
        // Handle max option
        let max = '9999px'
        if( _.startsWith( option, 'm' ) ) {
            max = option.split(':')[1]
            option = 'aspect'
            }
        // Calculate new height based on original aspect ratio,
        // but don't exceed max
        const viz_width = viz.videoWidth || viz.width
        const viz_height = viz.videoHeight || viz.height
        if( viz_height && _.startsWith( option, 'a' ) ) {
            container.addClass('es_hero_height')
            const aspect = viz_width / viz_height
            height = container.width() / aspect + 'px'
            }
        // Fold fills the top of fold (between header and bottom)
        else if( _.startsWith( option, 'f' ) ) {
            container.addClass('es_hero_fold')
            height = vh_portal + 'vh'
            }
        // Place into background of fold
        else if( _.startsWith( option, 'b' ) ) {
            container.addClass('es_hero_background')
            height = vh_portal + 'vh'
            if( _.startsWith( option, 'backfold') ) {
                container.css({ 'position': 'absolute' })
            } else {
                container.css({ 'position': 'fixed' })
                }
            }
        // Text lets container determine the height
        else if( _.startsWith( option, 'a' ) ) {
            container.addClass('es_hero_aspect')
            }
        // Support supressing image display
        else if( _.startsWith( option, 'n' ) ) {
            container.addClass('es_hero_none')
            }
        // Use whatever CSS height provided
        // For more complex styling, they can just use custom CSS
        else if( _.startsWith( option, 'c' ) ) {
            const css = option.split(':')[1]
            container.css({ 'height': css })
            height = ''
            }
        else {
            container.addClass('es_hero_text')
            height = ''
            }
        // Most cases just height is modified
        if( height ) {
            container.css({ 'height': 'min(' + max + ',' + height + ')' })
            }
        }

    function center_fixed_image( element, image ) {
    /*
        Given an element and a fixed position image, provide
        size and position CSS strings to scale and center.
    */
        const container = $( element )
        if( !( image && image.width && container.width() ) ) {
            return
            }
        // If image is loaded and container has a size, calculate size and center
        const view = $( window )
        // Figure fixed position of top-left corner of image
        // HACK add -1 to ensure rounding errors don't cause white lines
        const x = container.offset().left - 1
        const y = container.offset().top - 1
        // The size of the visible portal
        const width = Math.min( view.width(), container.width() )
        const height = Math.min( view.height(), container.height() )
        // Default to scaling height
        let size = 'auto ' + height + 'px'
        let position = 'center ' + y + 'px'
        // If width different bigger scale to it
        const diff_width = ( width - image.width ) / image.width
        const diff_height = ( height - image.height ) / image.height
        if( diff_width > diff_height ) {
            size = '100% auto'
            // Adjust y offset to center of image by width scaling
            const y_center = y + ( container.height() / 2 )
            const image_center = (image.height * (1 + diff_width)) / 2
            const y_top = y + Math.min( 0, y_center - image_center )
            position = 'center ' + y_top + 'px'
            }
        return { 'size': size, 'position': position,
                    'width': diff_width * width }
        }

    })();

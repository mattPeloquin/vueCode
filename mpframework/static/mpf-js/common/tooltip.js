/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extension of tippy/popper tooltips
*/
(function() { 'use strict';

    mp.HELP_STAFF_SELECTOR = ".mp_help_staff"
    const HOVER_DELAY = 800
    const TOUCH_DELAY = 400
    const MESSAGE_DURATION = 800

    mp.show_tooltip = function( element, message, options ) {
    /*
        Programatically show a one-time message on element
    */
        tippy( element, _.extend( {}, {
                content: message,
                interactive: true,
                showOnCreate: true,
                delay: [ 0, MESSAGE_DURATION ],
                onHidden: function( instance ) {
                    instance.destroy()
                    }
                },
            options ) )
        }


    mp.init_tooltips = function( element, options, message ) {
    /*
        Setup tooltips defined in static or dynamic HTML.
        Only display tooltip if text is present.
    */
        options = _.extend( {
                onShow: ( instance ) => {
                    return !!instance.props.content
                    },
                allowHTML: true,
                interactive: true,
                touch: [ 'hold', TOUCH_DELAY ],
                delay: [ HOVER_DELAY, 0 ],
                },
            options )
        // Look for a parent boundary
        if( element ) {
            const parent_boundary = $( element ).parents(".mp_tooltip_boundary")[0]
            if( parent_boundary ) {
                _.extend( options, {
                    popperOptions: { modifiers: [ {
                        name: 'preventOverflow',
                        options: { altAxis: true, boundary: parent_boundary },
                        }, {
                        name: 'flip',
                        options: { boundary: parent_boundary },
                        }, ] },
                    })
                }
            }
        else {
            element = window.document.body
            }
        // Setup either single message element with default options
        if( message ) {
            tippy( element, _.extend( {}, options, {
                content: message,
                 }))
            }
        // Or children based on tooltip CSS and data
        else {
            // Setup the different types of tooltips
            tippy( element.querySelectorAll('.mp_tooltip'), _.extend( {}, options, {
                content: get_tooltip_content(),
                }))
            tippy( element.querySelectorAll('.mp_tooltip_fast'), _.extend( {}, options, {
                content: get_tooltip_content(),
                delay: [ 0, 0 ],
                trigger: 'mouseenter click',
                touch: 'hold',
                }))
            tippy( element.querySelectorAll('.mp_tooltip_dynamic'), _.extend( {}, options, {
                onShow: function( instance ) {
                    instance.setContent( get_tooltip_content() )
                    return !!instance.props.content
                    },
                }))
            tippy( element.querySelectorAll('.mp_info'), _.extend( {}, options, {
                content: get_tooltip_content('fa fa-info-circle'),
                delay: [ 0, 0 ],
                trigger: 'click',
                }))
            }
        // Only want click on popup to close the popup
        $( element ).on( 'click', "[data-tippy-root]", function( e ) {
            e.stopPropagation()
            })
        }

    function get_tooltip_content( css ) {
    /*
        Factory for getting tooltip text embedded in HTML programattically or
        manually. Takes from title or ONE embedded mp_tooptip element
        that is a direct child.
    */
        css = css || ''
        function _get_content( tooltip ) {
            // HACK - minor side effect of adding class name
            tooltip.className += ( ' ' + css )
            // Check title first, then JS text, then element
            // Assume only one type provided, never choke
            let rv = false
            try {
                let tip = tooltip.getAttribute('title')
                if( tip ) {
                    rv = tip
                    tooltip.removeAttribute('title')
                    }
                if( !rv ) {
                    const tname = tooltip.getAttribute('tooltip')
                    if( tname ) {
                        rv = mpt[ 'tooltip_' + tname ]
                        }
                    }
                if( !rv ) {
                    tip = $( tooltip ).children("tooltip")
                    if( !tip.length ) {
                        tip = $( tooltip ).children(".mp_control").children("tooltip")
                        }
                    if( tip.length ) {
                        rv = tip.html()
                        }
                    }
                }
            catch( e ) {
                mp.log_error("Error getting tooltip content:", e)
                }
            return rv
            }
        return _get_content
        }

    })();

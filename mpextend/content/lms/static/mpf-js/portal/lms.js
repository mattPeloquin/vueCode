/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Customization and additions for LMS
*/
(function() { 'use strict';

    mpp.init_lms = function() {
        mpp.access_handlers['lmsitem'] = _play_lms
        }

    function _play_lms( item, tree_id, launcher ) {
    /*
        Setup lms item in the viewer frame in case it is accessed directly
        (if launched in separate frame, this won't be used)
    */
        function lms_launcher( access ) {
            mpl.start_lms_item( access.item )
            return launcher( access )
            }
        return item.request_access( lms_launcher, tree_id )
        }

    /*
        Fixup content height in iframe viewer
        HACK - Hardcoded assumptions for Storyline and Captivate content
    */
    _.extend( mpp.viewer_content_height, {
        'lmsitem': function( iframe_html ) {
            return _lms_content( iframe_html )
            }
        })

    function _lms_content( parent ) {
        // Captivate detection
        let rv = $( parent ).find("#cpDocument")
        if( !rv || !rv.length ) {
            // Storyline detection
            rv = $( parent ).find("#presentation-container")
            if( !rv || !rv.length ) {
                const frame = $( parent ).find("frame")
                rv = frame.contents().find("table")
                if( !rv || !rv.length ) {
                    rv = frame.contents().find(".framewrap")
                    }
                }
            }
        return rv && rv.length && rv[0]
        }

    mpp.lms_fixup = function( parent ) {
    /*
        Make sure size is reset after load
    */
        mp.run_when_ready(
            function() { return !!_lms_content( parent ) },
            function lms_content() {
                try {
                    const lms_frame = _lms_frame( parent )
                    mp.log_info("Fixing up lms: ", lms_frame)
                    $( lms_frame )
                        .on( 'load', function() {
                            mp.layout_resize()
                            })
                    }
                catch( e ) {
                    mp.log_error("Exception fixing up lms:", e)
                    }
                })
        }

    function _lms_frame( parent ) {
        // Captivate detection
        let rv = $( parent ).find("#cpDocument")
        if( !rv ) {
            // Storyline detection
            rv = $( parent ).find("frame")
            }
        return rv && rv.length && rv[0]
        }

    })();

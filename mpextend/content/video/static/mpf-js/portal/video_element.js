/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Customization and additions to the native HTML5 video player.
    These used both with native HTML5 player and additional viewers.
*/
(function() { 'use strict';

    const LOCAL_TIME_UPDATE_FREQ = 4000

    mpp.video_fixup = function( parent ) {
    /*
        Setup video control inside parent
    */
        mp.run_when_ready(
            function() { return !!$( parent ).find("video")[0] },
            function video_setup() {
                return _video_setup( parent )
                }
            )
        }

    function _video_setup( parent ) {
    /*
        Find first video element under parent and fix it up when ready
    */
        try {
            mp.log_info("Fixing up video player:", parent)
            $( parent ).find("video")
                .on( 'loadeddata', function( event ) {
                    mp.log_info("VIDEO PLAYING: ", mpp.vm_current.item().name,
                                    " -> " + event.target.currentSrc)
                    mpp.vm_current.item().model.trigger('user_started')
                    mp.layout_resize()
                    })
                .on( 'timeupdate', _.throttle( function( event ) {
                    // Timeupdate called a LOT, so back it off some
                    mpp.vm_current.item().model.trigger(
                        'user_progress', event.target.currentTime )
                    }, LOCAL_TIME_UPDATE_FREQ )
                    )
                .on( 'ended', function( event ) {
                    mp.log_info("VIDEO COMPLETED: ", mpp.vm_current.item().name)
                    mpp.vm_current.item().model.trigger('user_completed')
                    // Move on to the next item if possible
                    mpp.next_core_item( function( item, node ) {
                        if( !mpp.sb_option( 'portal.no_play_next', null, node ) ) {
                            item.user_access_action( node )
                            }
                        })
                    })
            }
        catch( e ) {
            mp.log_error("Video player exception:", e)
            }
        }

    })();

/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extends videojs which should already be loaded.
    RUNS IN IFRAME from video_videojs.chtml to support communication with framework
    and saving preferences, so only scripting loaded there is available.

    This is in ADDITION to native event listeners in portal/video_element.js
    Viewer preferences are kept in per-user localStorage, to persist for each device.
    Shadowing server user data uses sessionStorage, to provide higher-resolution
    memory of video location than is provided in user and visitor support,
    while not cluttering up browser with short-term info.
*/
(function(mpv) { 'use strict';

    const HEIGHT_MAX_ADJ = 0.9

    const player = videojs(
            "video_videojs", {
                autoplay: false,
                preload: 'auto',
                controls: true,
                fluid: true,
                responsive: true,
                playbackRates: [ 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2.0 ],
                controlBar: {
                    },
                poster: mpv.player_poster,
                },
            // Pass set source here to prevent occasional strangeness from
            // loading video and then starting videojs (in Firefox)
            set_player_source
            )
    const video_key = 'mpvideo_time_' + mpv.item.id

    function set_player_source() {
        // Set player to default (first) item it any exist
        const item = mpv.player_sources[0]
        if( !item ) {
            mp.log_error("VIDEO no content for: " + mpv.item.name)
            }
        player.src({
            type: item.content_type,
            src: item.url,
            })
        }

    // Always start in fluid mode to try to fill container
    $("body").toggleClass( 'mp_videojs_fluid', true )

    $( window ).on( 'resize orientationchange', function() {
        // FUTURE - add some edge cases for video resize
        })

    mpv.update_video = function( access ) {
    /*
        Change source for video based on access session
    */
        mpv.item = access.item
        mpv.player_sources = access.direct.player_sources
        mpv.player_poster = access.direct.poster_url
        mpv.progress_data = access.progress_data
        set_player_source()
        }

    // FUTURE - Add new silvermine quality and casting plugins
    //player.videoJsResolutionSwitcher()

    player.on( 'loadedmetadata', function() {
        // Setup how CSS for player will display based on aspect ratios
        set_video_responsive_mode()
        // Set video to current play position
        player.currentTime( get_position( player.duration() ) )
        if( mpp.auto_play ) {
            player.play()
            }
        })
    player.on( 'loadeddata', function( event ) {
        // Restore preferences
        player.volume( mp.local_get('ui').mpvideo_volume )
        player.muted( mp.local_get('ui').mpvideo_muted )
        player.playbackRate( mp.local_get('ui').mpvideo_speed )
        })
    player.on( 'timeupdate', function( event ) {
        // MPF is responding to event and saving in user data;
        // duplicate here for local higher-resolution capture
        sessionStorage.setItem( video_key, player.currentTime() )
        })
    player.on( 'ended', function( event ) {
        // Remove video progress, so it starts at begining
        sessionStorage.removeItem( video_key )
        })
    player.on( 'error', function( event ) {
        // Place error with videojs instead of on native to get better info
        const error = player.error()
        mp.log_error("VIDEO: " + error.message)
        mp.log_phone_home('VIDEO', error.message)
        })

    // MONKEY PATCHES - Save/Set with some sanity checks
    const _orig_volume = player.volume
    player.volume = function( vol ) {
        if( vol === null ) vol = undefined
        if( vol !== undefined ) {
            vol = Math.min( 1, Math.max( 0, vol ) )
            mp.local_update( 'ui', { mpvideo_volume: vol } )
            }
        return _orig_volume.call( this, vol )
        }
    const _orig_muted = player.muted
    player.muted = function( mute ) {
        if( mute === null ) mute = undefined
        if( mute !== undefined ) {
            mute = ( mute !== false && mute !== "false" )
            mp.local_update( 'ui', { mpvideo_muted: mute } )
            }
        return _orig_muted.call( this, mute )
        }
    const _orig_playbackRate = player.playbackRate
    player.playbackRate = function( rate ) {
        if( rate === null ) rate = undefined
        if( rate !== undefined ) {
            rate = Math.min( 4, Math.max( 0.4, rate ) )
            mp.local_update( 'ui', { mpvideo_speed: rate } )
            }
        return _orig_playbackRate.call( this, rate )
        }

    function set_video_responsive_mode() {
    /*
        For most viewer modes, video works best when videojs fluid mode
        is used when video aspect ratio exceeds the screen's aspect ratio.
        Otherwise use fill mode along with CSS for setting height
        Fluid fills width of viewport, height of container follows.
        Think of skinny phone video on a wide laptop screen; in fluid mode
        only a small part of the top is visible and controls aren't seen.
    */
        let aspect_ratio = 1.6
        if( player.videoHeight() ) {
            aspect_ratio = player.videoWidth() / player.videoHeight()
            }
        // See if the current iframe HTML maximizes use of the video aspect ratio,
        // adjust to max height if not
        let width = $(":root").width()
        let height = $(":root").height()
        if( aspect_ratio > 1 ) {
            if( height * aspect_ratio < width ) {
                height = Math.floor( width / aspect_ratio )
                let screen_height = height
                try {
                    screen_height = $( window.top ).height() * HEIGHT_MAX_ADJ
                } catch( e ) {
                    mp.log_debug("Couldn't get screen height")
                    }
                $(":root").height( Math.min( height, screen_height ) )
                }
            }
        let screen_aspect = 1
        if( $(":root").height() ) {
            screen_aspect = $(":root").width() / $(":root").height()
            }

        const fluid = screen_aspect < aspect_ratio
        player.fluid( fluid )
        player.fill( !fluid )
        $("body")
            .toggleClass( 'mp_videojs_fluid', fluid )
            .toggleClass( 'mp_videojs_fill', !fluid )
            .attr({ 'data-aspect_ratio': aspect_ratio })
        }

    function get_position( duration ) {
    /*
        Returns position for current video
        Give local storage precedence, as it is updated the most often,
        then use the last stored DB value from loading the player.
        Assumes progress data is storing the number of seconds for current
        spot in video.
        Reset to zero if bad values are found
    */
        let saved_position = sessionStorage.getItem( video_key ) || mpv.progress_data
        const end_buffer = duration && duration - 4
        if( end_buffer && saved_position && saved_position > end_buffer ) {
            saved_position = 0
            }
        return saved_position || 0
        }

})(window.mpv = window.mpv || {});

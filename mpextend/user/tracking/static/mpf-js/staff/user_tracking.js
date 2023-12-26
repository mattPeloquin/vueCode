/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Support mapping of user info in Google Maps v3.
    Loaded directly into the user dashboard page.

    PORTIONS ADAPTED FROM OPEN SOURCE:
      django-tracking -- MIT License
      Copyright (c) 2008-2009 Josh VanderLinden
      https://bitbucket.org/codekoala/django-tracking
*/
'use strict';

let user_map = null
let info_window = null
let user_list = {}

mp.when_ui_loaded( function init_map() {
    try {
        // Google Maps options (see google maps V3)
        const mapOptions = {
            center: new google.maps.LatLng( 25, 10 ),
            mapTypeId: google.maps.MapTypeId.HYBRID,
            streetViewControl: false,
            scrollwheel: false,
            zoom: 2,
            }
        user_map = new google.maps.Map( $('#user_map')[0], mapOptions )
        info_window = new google.maps.InfoWindow()
        // Make sure map is filling div
        google.maps.event.trigger( user_map, 'resize' )
        }
    catch( e ) {
        mp.log_error("Google maps not loaded: ", e)
        }
    })

function add_user( _index, user ) {

    user.mins = ( user.seconds / 60 ).toFixed(1)
    user.hours_ago = ( user.last_update / 60 ).toFixed(1)

    // If the user is not already in the cache, add to display
    if( !user_list[ user.id ] ) {
        create_list_item( user )
        user_list[ user.id ] = { 'id': user.id, 'marker': create_marker( user ) }
        }

    // Otherwise just update list values for item that are most likely to change
    else {
        $('#user_url-' + user.id).html( user.url )
        $('#user_mins-' + user.id).html( user.mins )
        $('#user_hours_ago-' + user.id).html( user.hours_ago )
        // Send recently-active users to the top of the list (last update is in minutes)
        if (user.sessions_active && user.last_update <= 30) {
            $('#user-' + user.id).prependTo( $('#user_list') )
            }
        }
    }

function create_list_item( user ) {
    const list_html =
        `<div id="user-${ user.id }">
            <span class="user_email">${ user.email } - </span>
            <span id="user_sessions-${ user.id }">${ user.sessions_active }</span>
                active sessions over ${ user.days_ago } days
             <span id="user_mins-${ user.id }">${ user.mins }</span> minutes,
             <span id="user_hours_ago-${ user.id }">${ user.hours_ago }</span> hours ago
            </span></div>`

    $('#user_list').prepend( list_html )

    // Add popup for mouse over of list item
    $('#user-' + user.id).click( function() {
        mp.dialog_html( popup_text(user) )
        })
    }

function create_marker( user ) {
    if( user.geoip && user.geoip.location ) {
        const marker = new google.maps.Marker({
            map: user_map,
            position: new google.maps.LatLng( user.geoip.location.latitude,
                        user.geoip.location.longitude ),
            icon: mpurl.map_tracking,
            animation: google.maps.Animation.DROP,
            title: user.email + ' (' + user.geoip.location.city + ')',
            })

        // Add pop up info box when the mouse goes over a marker
        google.maps.event.addListener( marker, 'click', function() {
            info_window.setContent( popup_text(user) )
            info_window.open( user_map, marker )
            })

        return marker
        }
    mp.log_debug("No geo info, so no map marker: ", user)
    }

function popup_text( user ) {
    const geo = user.geoip ?
        `<div>${ user.geoip.location.city } ${ user.geoip.location.region.name } ${ user.geoip.country }</div>`
        : ''
    return `<div class="user_map_overlay">
        <div class="user_email">${ user.email } ${ user.name != user.email ? user.name : '' }</div>
        ${ geo }
        <div>IP address: ${ user.ip }</div>
        <div class="user_url">Last url: ${ user.url }</div>
        <div>${ user.browser }</div>
        </div>`
    }

function clean_old_markers( new_users ) {
    const new_user_ids = _.map( new_users, 'id' )
    $.each( user_list,
        function( id, user_info, index ) {
            const marker = user_info ? user_info['marker'] : null
            if( marker && !_.includes( new_user_ids, id )) {
                $('#user-' + id).remove()
                marker.setMap( null )
                user_list[ index ] = null
                }
            })
    }

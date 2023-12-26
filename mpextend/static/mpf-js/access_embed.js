/*--- Mesa Platform, Copyright 2021 Vueocity, LLC
    Script included for accessing embedded content from different domains.
*/
(function() {
    if( window.mesa_platform ) {
        return
        }
    window.mesa_platform = {
        PAGE_PREFIX: "",
        ACCESS_PREFIX: "",
        CLOSE_TEXT: "Close",
        }
    const PORTAL_PREFIX = '/portal'
    const DEFAULT_LOGIN_WIDTH = 360
    const DEFAULT_LOGIN_HEIGHT = 440
    const LOGIN_POLL_INTERVAL = 250

    // Style injected into page holding embeds
    try {
        const style = document.createElement('style')
        style.setAttribute( 'mesa-platform-stylesheet', '' )
        style.textContent = `
            .es_access_button {
                display: block; padding: 0.4em 0.8em; border-radius: 0.2em;
                color: white; background-color: rgba(0,49,225,0.6);
                }
            .es_access_widget .es_access_iframe.es_access_small {
                height: 16em;
                }
            .es_access_widget .es_access_iframe.es_access_large {
                width: 90vw; height: 66vh;
                }
            .es_access_window {
                display: block; z-index: 999999; visibility: visible;
                position: fixed; left: 0px; top: 0px; width: 100%; height: 100%;
                overflow-x: hidden; overflow-y: auto; margin: 0; padding: 0;
                background: rgba(66,66,66,0.8);
                }
            .es_access_widget .es_access_close { display: none; }
            .es_access_window .es_access_close {
                display: block !important; visibility: visible; z-index: 2;
                position: absolute; right: 2vw; top: 8vh;
                border: 0px none transparent; border-radius: 0.2em;
                margin: 0; padding: 0.2em 0.4em;
                color: white; background-color: rgba(120,120,120,0.8);
                }
            .es_access_window .es_access_iframe {
                display: block; visibility: visible;
                position: absolute; left: 5vw; top: 10vh;
                width: 90vw !important; height: 85vh !important;
                overflow-x: hidden; overflow-y: auto; margin: 0; padding: 0;
                background: transparent; border: 0px none transparent;
                border-radius: 0.2em; -webkit-tap-highlight-color: transparent;
                }
            :is(.es_access_button,.es_access_close):is(:hover,:focus,:active) {
                cursor: pointer; background-color: rgba(0,49,225,0.8);
                }`
        const head = document.getElementsByTagName('head')[0]
        head.appendChild( style )
        }
    catch( e ) {
        console.error( e )
        }

    // Set attributes for page holding embed
    document.querySelectorAll('.mp_access_button').forEach(
        function init_button( element ) {
            try {
                // Setup button
                const is_page = element.classList.contains('es_access_page')
                element.classList.add('es_access_button')
                element.addEventListener( 'click', function( event ) {
                    event.preventDefault()
                    is_page ? button_window( element ) : button_iframe( element )
                    })
                if( !element.innerHTML.trim() ) {
                    const url = element.getAttribute('href')
                    const slug = element.getAttribute('data-slug')
                    const host = url.slice( 0, url.indexOf( PORTAL_PREFIX ) )
                    fetch( host + '/api/public/content/partial/' + slug  )
                        .then( response => response.json() )
                        .then( data => {
                            element.innerHTML = is_page ? mesa_platform.PAGE_PREFIX :
                                        mesa_platform.ACCESS_PREFIX
                            element.innerHTML += data.name
                            })
                    }
                }
            catch( e ) {
                console.error( e )
                }
            })
    document.querySelectorAll('.mp_access_widget').forEach(
        function init_widget( element ) {
            // Replace widget placeholder with pane for iframe, with close if popup
            try {
                const pane = document.createElement('mp_pane')
                pane.setAttribute( 'class', 'es_access_widget' )
                // Create new iframe
                const iframe = create_iframe( element )
                pane.appendChild( iframe )
                // Insert new pane
                const location = element.parentElement
                const prevSib = element.previousElementSibling || location.firstElementChild
                location.insertBefore( pane, prevSib )
                // Add close button to reset pane popup CSS and reload content iframe
                if( element.classList.contains('es_access_popup') ) {
                    const close = document.createElement('div')
                    close.setAttribute( 'class', 'es_access_close' )
                    close.innerHTML = mesa_platform.CLOSE_TEXT
                    close.addEventListener( 'click', function() {
                        pane.classList.remove('es_access_window')
                        iframe.src = iframe.src;
                        })
                    pane.appendChild( close )
                    }
                element.remove()
                }
            catch( e ) {
                console.error( e )
                }
            })

    // Messages from embedded iframes
    window.addEventListener( 'message', function iframe_events( event ) {
        try {
            if( event.data.mp_event_login_url ) {
                // Popup sign-in centered on screen
                const width = mp.sb_options.site.login_width || DEFAULT_LOGIN_WIDTH
                const height = mp.sb_options.site.login_height || DEFAULT_LOGIN_HEIGHT
                const top = ( window.innerHeight / 2 ) - ( height / 2 ) +
                            window.screenTop
                const left = ( window.innerWidth / 2 ) - ( width / 2 ) +
                            window.screenLeft
                const opts = `titlebar=no, toolbar=no, resizeable=yes,
                        width=${ width }, height=${ height }, top=${ top }, left=${ left }`
                open_login( event.data.mp_event_login_url, opts )
                }
            if( event.data.mp_event_user_access ) {
                // Make embedded widget into popup access window
                const data = event.data.mp_event_user_access
                const iframe = document.getElementById(`mp_access_${ data.node || data.slug }`)
                if( iframe.classList.contains('es_access_popup') ) {
                    iframe.parentElement.classList.add('es_access_window')
                    }
                }
            }
        catch( e ) {
            console.error( e )
            }
        })

    function button_window( element ) {
        window.open( element.getAttribute('href'), '_blank' )
        }
    function button_iframe( element ) {
        // Put close button and iframe onto pane and place over screen
        const pane = document.createElement('mp_pane')
        pane.setAttribute( 'class', 'es_access_window' )
        const close = document.createElement('div')
        close.setAttribute( 'class', 'es_access_close' )
        close.innerHTML = mesa_platform.CLOSE_TEXT
        close.addEventListener( 'click', function() {
            pane.remove()
            })
        pane.appendChild( close )
        // Place new iframe under pane at top of the body
        const iframe = create_iframe( element )
        pane.appendChild( iframe )
        document.body.insertBefore( pane, document.body.firstChild )
        document.getElementById( iframe.getAttribute('id') ).focus()
        }

    function create_iframe( element ) {
        const iframe = document.createElement('iframe')
        const id = element.getAttribute('data-slug') || element.id
        const url = element.getAttribute('href') || element.getAttribute('src')
        iframe.setAttribute( 'id', 'mp_access_' + id )
        iframe.setAttribute( 'src', url )
        iframe.setAttribute( 'class', 'es_access_iframe mp_access_iframe ' +
                element.getAttribute('class') )
        iframe.setAttribute( 'allow', 'fullscreen' )
        iframe.onload = function iframe_load() {
            // Send iframe information about how it's being used
            const classList = element.classList
            iframe.contentWindow.postMessage({
                mp_event_iframe_init: {
                    access_button: classList.contains('es_access_button'),
                    access_small: classList.contains('es_access_small'),
                    access_large: classList.contains('es_access_large'),
                    access_popup: classList.contains('es_access_popup'),
                    }
                }, '*' )
            }
        return iframe
        }

    // Detect user login and refresh iframes
    let login = null
    function open_login( url, opts ) {
        if( login ) {
            login.close()
            }
        login = window.open( url, '_blank', opts )
        if( login ) {
            login.focus()
            }
        else {
            console.error("Could not open login window")
            }
        }
    function check_login() {
        if( login && login.closed ) {
            document.querySelectorAll('.mp_access_iframe')
                .forEach( function( element ) {
                    element.src = element.src
                    })
            login = null
            }
        setTimeout( check_login, LOGIN_POLL_INTERVAL )
        }
    check_login()

    })();

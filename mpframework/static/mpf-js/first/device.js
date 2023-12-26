/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Lightweight debugging and log analysis for MAJORITY USE DEVICES.
    Brief, APPROXIMATE, human-friendly and parsable description of
    KEY DEVICE CHARACTERISTICS.

    NOT used for any client-side behavior.
    Not an exhaustive look at the user-agent string or device
    capabilities (which is done on server for debug/tracking).

    FUTURE - Make sure this works ok as Chrome starts to retire UA string

    PORTIONS ADAPTED FROM OPEN SOURCE:
        https://github.com/html5crew/ua_parser/blob/master/src/js/ua_parser.js
*/
(function() { 'use strict';

    function browser( ua ) {
        let match =
                /(edg)[e \/]([\w.]+)/.exec( ua ) ||
                /(chrome)[ \/]([\w.]+)/.exec( ua ) ||
                /(webkit)(?:.*version)?[ \/]([\w.]+)/.exec( ua ) ||
                /(msie) ([\w.]+)/.exec( ua ) ||
                ua.indexOf("compatible") < 0 && /(mozilla)(?:.*? rv:([\w.]+))?/.exec( ua ) ||
                [ "", "other", "version unknown" ]
        if( match[1] === "webkit" ) {
            match = /(iphone|ipad|ipod)[\S\s]*os ([\w._\-]+) like/.exec( ua ) ||
                /(android)[ \/]([\w._\-]+);/.exec( ua ) ||
                [ "", "safari", match[2] ]
            }
        else if( match[1] === "mozilla" ) {
            if( /trident/.test(ua) ) {
                match[1] = "msie-trident"
                }
            else {
                match[1] = "firefox"
                }
            }
        return {
            name: match[1],
            version: match[2]
            }
        }

    function os( ua ) {
        let match =
            /(iphone|ipad|ipod)[\S\s]*os ([\w._\-]+) like/.exec( ua ) ||
            /(windows)(?: nt | phone(?: os){0,1} | )([\w._\-]+)/.exec( ua ) ||
            /(android)[ \/]([\w._\-]+);/.exec( ua ) ||
            /(mac) os x ([\w._\-]+)/.exec( ua ) ||
            /(cros)(?:\s[\w]+\s)([\d._\-]+)/.exec( ua ) ||
            (/(linux)/.test( ua ) ? [ "", "linux", "0.0.0" ] : false ) ||
            [ "", "unknown", "0.0.0" ]
        return {
            name: match[1],
            version: match[2]
            }
        }

    function mobile( ua ) {
        return !!ua.match(/mobi/)
        }

    function touch() {
        return !!navigator.maxTouchPoints
        }

    try {
        const ua = window.navigator.userAgent.toLowerCase()
        mp.device = {
            ua: ua,
            browser: browser( ua ),
            mobile: mobile( ua ),
            os: os( ua ),
            touch: touch(),
            }
        mp.device.desc =
            mp.device.browser.name + "(" + mp.device.browser.version + ")" +
            ( mp.device.mobile ? " mobile " : " " ) +
            mp.device.os.name + "(" + mp.device.os.version + ")" +
            ( mp.device.touch ? " touch " : " " ) +
            screen.width + "x" + screen.height
        }
    catch( e ) {
        mp.log_info("Device detect exception:", e)
        mp.device = {
            desc: "unknown device"
            }
        }

    })();

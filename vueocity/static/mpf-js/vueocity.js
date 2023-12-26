/*--- Vueocity Platform, Copyright 2021 Vueocity, LLC

    Utilities for Vueocity UI additions
*/
'use strict';


mp.HELP_STAFF_SELECTOR += ',#onboard_help,#tutorial_tool'


mp.get_tz_offset = function() {
/*
    Returns the timezone offset in the client
*/
    const current_date = new Date()
    let current_timeoffset = current_date.getTimezoneOffset()
    if( current_date.dst() ) {
        current_timeoffset += -60
        }
    return current_timeoffset
    }

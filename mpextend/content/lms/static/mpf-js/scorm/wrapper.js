/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Wrap the playing of SCORM lessons to respond to either
    SCORM 2004 or SCORM 1.2 events MPF cares about
    and gracefully ignore others

    The main goal is to make sure SCORM lessons play vs. blowing up, so
    if there is a choice between compliance vs. moving playing, just play

    PORTIONS ADAPTED FROM OPEN SOURCE:
        SCORM RTS (LMS) by Ondej Medek under Poetic License
        https://sites.google.com/site/xmedeko/code/misc/simple-javascript-scorm-2004-api
*/
(function(mpl) { 'use strict';

    mpl.Api = function( type ) {

        // Hold the current error state for the wrapper
        this.error = 0

        // Hold current initialization state
        this.STATE = {
            NOT_INITIALIZED : "Not Initialized",
            RUNNING : "Running",
            TERMINATED : "Terminated"
            }
        this.state = this.STATE.NOT_INITIALIZED

        /*
            Initial state of values that lessons may request
            These values need to be set to not have anything blow up when playing
            lessons across the various SCORM publishing frameworks
            (e.g., Captivate 9 started blowing up with resume_date undefined in 2016)
                http://scorm.com/scorm-explained/technical-scorm/run-time/
                http://scorm.com/scorm-explained/technical-scorm/run-time/run-time-reference/
        */
        this.cmi = {

            // SCORM 2004
            'cmi.success_status' : 'unknown',
            'cmi.completion_status' : 'incomplete',
            'cmi.score.scaled' : '0',
            'cmi.session_time' : '',
            'cmi.location' : '',
            'cmi.entry' : 'resume',
            'cmi.suspend_data' : '',
            'cmi.mode' : 'normal',
            'cmi.credit' : 'credit',

             // SCORM 1.2
            'cmi.core.lesson_status' : 'incomplete',
            'cmi.core.score.raw' : '0',
            'cmi.core.session_time' : '',
            'cmi.core.lesson_location' : '',
            'cmi.core.entry' : 'resume',
            'cmi.core.lesson_mode' : 'normal',
            'cmi.core.credit' : 'credit',
            'cmi.suspend_data' : '',
            'cmi.score._children' : 'scaled,min,max,raw',
            'cmi.interactions._children' : 'id,type,result,description',
            'cmi.interactions._count' : '0',

            'cmi._version' : 'MPF1.1',
            }

        // Implementation
        this._type = type
        this._valuesChanged = {}
        this._valueNameSecurityCheck = function( name ) {
            this.error = name.search( /^cmi\.(\w|\.)+$/ ) === 0 ? 0 : 401
            return this.error === 0
            }
        this._check_running = function( errBefore, errAfter ) {
            if( this.state === this.STATE.NOT_INITIALIZED ) {
                this.error = errBefore
                }
            else if( this.state === this.STATE.TERMINATED ) {
                this.error = errAfter
                }
            else {
                this.error = 0
                }
            return this.error === 0
            }
        }

    // Scorm 2004 API
    mpl.Api.prototype.Initialize     = Initialize
    mpl.Api.prototype.Terminate      = Terminate
    mpl.Api.prototype.GetValue       = GetValue
    mpl.Api.prototype.SetValue       = SetValue
    mpl.Api.prototype.Commit         = Commit
    mpl.Api.prototype.GetLastError   = GetLastError
    mpl.Api.prototype.GetErrorString = GetErrorString
    mpl.Api.prototype.GetDiagnostic  = GetDiagnostic

    // Scorm 1.2 API
    mpl.Api.prototype.LMSInitialize     = Initialize
    mpl.Api.prototype.LMSFinish         = Terminate
    mpl.Api.prototype.LMSGetValue       = GetValue
    mpl.Api.prototype.LMSSetValue       = SetValue
    mpl.Api.prototype.LMSCommit         = Commit
    mpl.Api.prototype.LMSGetLastError   = GetLastError
    mpl.Api.prototype.LMSGetErrorString = GetErrorString
    mpl.Api.prototype.LMSGetDiagnostic  = GetDiagnostic


    function Initialize() {
        mp.log_info("MPLMS-Initialize:", this._type)
        if( this.state === this.STATE.TERMINATED ) {
            this.error = 104
            return 'false'
            }

        // Have seen different behaviors from different scorm packages;
        // in general go with acceptance of initialization
        this.state = this.STATE.RUNNING
        this.error = 0

        // Load up lesson resume data now
        const progress_data = mpl.current_item.get('progress_data')
        mp.log_debug("MPLMS-GetValue:", progress_data)
        this.cmi['cmi.suspend_data'] = progress_data

        mpl.current_item.trigger('lms_started')

        return 'true'
        }

    function Terminate() {
        mp.log_debug("MPLMS-Terminate")
        if( !this._check_running(112, 113) ) return 'false'

        this.Commit()
        this.state = this.STATE.TERMINATED

        return 'true'
        }

    function GetValue( name ) {
        mp.log_debug("MPLMS-GetValue:", name)
        if( !this._check_running(122, 123) ) return ''
        if( !this._valueNameSecurityCheck(name) ) return ''
        let rv = this.cmi[ name ]
        if( typeof rv === 'undefined' ) {
            rv = ''
            }
        if( rv != '' ) mp.log_debug(" ", name, ": ", rv)
        return rv
        }

    function SetValue( name, value ) {
        // Record SetValue changes to be saved on next commit
        mp.log_debug("MPLMS-SetValue -", name, ":", value)
        if( !this._check_running(132, 133) ) return 'false'
        if( !this._valueNameSecurityCheck(name) ) return 'false'

        this._valuesChanged[ name ] = value
        mpl.value_event_dispatch( name, value )

        return 'true'
        }

    function Commit() {
        // Save the SetValue changes accumulated since last commit
        mp.log_debug("MPLMS-Commit:", JSON.stringify(this._valuesChanged))
        if( !this._check_running(142, 143) ) return 'false'

        _.extend( this.cmi, this._valuesChanged )
        this._valuesChanged = {}
        mpl.commit()

        return 'true'
        }

    function GetLastError() {
        if( this.error ) mp.log_debug("MPLMS-GetLastError return", this.error)
        return this.error
        }

    function GetErrorString( errCode ) {
        mp.log_debug("MPLMS-GetErrorString:", errCode)
        return _error_strings[errCode] ? _error_strings[errCode] : ''
        }

    function GetDiagnostic( errCode ) {
        mp.log_debug("MPLMS-GetDiagnostic:", errCode)
        if( !errCode ) return this.GetLastError()
        return _error_strings[errCode] ? _error_strings[errCode] : 'General error'
        }

    const _error_strings = {
        0 : "No error",

        101 : "General Exception",
        102 : "General Initialization Failure",
        103 : "Already Initialized",
        104 : "Content Instance Terminated",
        111 : "General Termination Failure",

        201 : "General Argument Error",
        301 : "General Get Failure",
        351 : "General Set Failure",
        391 : "General Commit Failure",

        1000 : "General communication failure (Ajax)"
        }

    })(window.mpl = window.mpl || {});

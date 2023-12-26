/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

   Root file for LMS wrapping
   This is used to manage Scorm iframes, which may be loaded directly in the
   viewer, or via a CF iframe depending on compatibility settings

*/
(function(mpl) {

    mpl.current_item = false

    mpl.start_lms_item = function( lms_item ) {
        mp.log_info("LMS ITEM STARTING: ", lms_item)

        // Active item model is tracked separately from mpp.vm_current.item
        // as this may be running in its own iframe
        mpl.current_item = lms_item

        // Create a new instance of API state for 2004 and 1.2, and assign
        // to window so the Scorm code being played can find it
        window.API = new mpl.Api( "SCORM 1.2" )
        window.API_1484_11 = new mpl.Api( "SCORM 2004" )
        }

    })(window.mpl = window.mpl || {});

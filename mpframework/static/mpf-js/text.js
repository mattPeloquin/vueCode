/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    UI text used in the client

    Split between system strings that are constants (uppercase),
    and SiteBuilder defaults that can be overridden (lowercase).

    Items relying on JS variables can be used, but are only
    initialized after script load.
*/

(function() {

    mpt.AJAX_ERROR = "Please try refreshing the page to renew your session"
    mpt.SERVER_ERROR = "There was a problem, please try refreshing the page"

    mpt.ITEM_NOT_CONFIGURED = `This item is not yet available, please contact ` +
                `${ mpurl.sandbox_support_email }`

    mpt.CLIPBOARD_HELP = "Copy to clipboard"
    mpt.CLIPBOARD_COPIED = "Copied!"

    mpt.REPORT_CHECK_DONE = `We're creating your report, please check ` +
                `${ mp.user.email } for download link`

    // Items accessed through sbt(), allowing for theme/content override

    mpt.signin = "Sign&nbsp;in"
    mpt.signup = "New&nbsp;account"

    mpt.empty = "There are no items to display"
    mpt.no_results = "No results"
    mpt.about = "About"

    mpt.back = "<&nbsp;Back"
    mpt.back_panel = ""   // overrides prefix panel message
    mpt.back_home = "<&nbsp;Home"
    mpt.back_prefix = "<&nbsp;"
    mpt.previous = "Previous"
    mpt.next = "Next"

    mpt.area_featured = "Featured items"
    mpt.area_core = "Main items"
    mpt.area_support = "Resources"
    mpt.area_custom1 = "Area 1"
    mpt.area_custom2 = "Area 2"
    mpt.area_custom3 = "Area 3"

    mpt.viewer_close = "Close viewer"

    mpt.access_title_select = "Select access option"
    mpt.access_title_confirm = "Confirm access option"
    mpt.access_title_notify = "Applying access option"
    mpt.access_title_problem = "Available soon"
    mpt.access_login = "I have an account"
    mpt.access_coupon = "Please select a purchase option and we'll" +
                "apply \"%code%\" to it"
    mpt.access_location = "Location of purchase"
    mpt.access_account_apply = "Apply license to account"
    mpt.access_signup = "Signup for "

    mpt.coupon_prompt = "I have a coupon code"
    mpt.coupon_apply = "Apply&nbsp;coupon"
    mpt.coupon_code = "Please enter a coupon code"
    mpt.coupon_invalid = "\"%code%\" is not a valid code"
    mpt.coupon_expired = "\"%code%\" has expired"

    mpt.content_size_title = "Duration:&nbsp;"
    mpt.content_size_unit = "hours"

    mpt.vm_item_status = {
        'no_state': "",
        'A':        "Accessed",
        'C':        "Completed",
        'S':        "In progress",
        'locked':   "Locked",
        'default':  "Available",
        }
    mpt.vm_item_action = {
        'action_none':     "",
        'action_viewer':   "View",
        'action_win':      "Open",
        'action_inline':   "Access",
        'action_download': "",
        }

    mp.sbt = function( name ) {
    /*
        For customizable text from sandbox options
    */
        let rv = ""
        try {
            rv = mp.sb_options.text[ name ]
            if( !rv ) {
                rv = mpt[ name ]
                }
            }
        catch( e ) {
            mp.log_error("Exception getting text: ", name, e)
            }
        return rv
        }

  })();

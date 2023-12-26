/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Parsley initialization
*/
(function() { 'use strict';

    $( document ).ready( function() {

        // Convert to EasyStyle
        Parsley.options.successClass = 'es_field_valid'
        Parsley.options.errorClass = 'es_field_error'
        Parsley.options.errorsWrapper = '<ul class="es_error_list"></ul>'

        // Register any ADMIN forms with parsley
    	// In debug extra forms get swept up in this, but who cares
        if( mp.is_page_admin ) {
            $('form')
                // Skip changelist form, as it will try to place items inline
                .not('#mp_changelist_form, #changelist-search-form')
                .each( function () {

                    // Turn on parsley validation for forms on a page
                    $(this).parsley({ excluded: _parsley_admin_excludes })

                        // HACK - Make sure Django select filters have items selected on submit
                        .on( 'form:submit', function () {
                            $('select[class^=filtered][id$=_to]').each( function () {
                                SelectBox.select_all( this.id )
                                })
                            })

                        // Open a closed admin section if there is an error
                        .on( 'field:error', function () {
                            $('.es_field_error').parents('.mp_module')
                                .removeClass('mp_closed')
                            })
                    })
            }

        // Setup listeners for additional UI display based on success/error
        // Dependent item needs es_field_valid/error_show class and
        // either under input item or have class with same name as input item
        function find_handler( field, type ) {
            const selector = '.es_field_' + type + '_show'
            const name = field.$element[0].name
            // Get any siblings with selector
            const valid = field.$element.siblings( selector )
            // Add any other items with selector and same name
            name && valid.add( selector + '.' + name )
            return valid
            }
        function find_valid( field ) {
            return find_handler( field, 'valid' )
            }
        function find_error( field ) {
            return find_handler( field, 'error' )
            }
        Parsley.on( 'field:error', function( field ) {
            find_valid( field ).addClass('mp_invisible')
            find_error( field ).removeClass('mp_invisible')
            })
        Parsley.on( 'field:success', function( field ) {
            find_valid( field ).removeClass('mp_invisible')
            find_error( field ).addClass('mp_invisible')
            })

        })

    const _parsley_admin_excludes = '' +

        // Parsley default excludes, which don't make sesne
        'input[type=button], input[type=hidden], input[type=submit], input[type=reset],' +

        // Disable on textareas as it causes proplems with editor screens
        'textarea,' +

        // Parsely not playing well with file uploads when files already uploaded, so pulling
        'input[type=file],' +

        // Make sure any disabled or readonly items don't have parsley
        ':disabled, input[readonly=readonly], input[tabindex=-1]'


    // Default parsley text has periods and lots of passive voice
    Parsley.addMessages('en', {

      defaultMessage: "This value is invalid"
      , type: {
            email:      "A valid email is needed here"
          , url:        "A valid url is needed here"
          , number:     "A number is needed here"
          , integer:    "A valid integer is needed here"
          , digits:     "This value should be digits"
          , alphanum:   "An alphanumeric value is needed here"
        }
      , notblank:       "This value cannot be empty"
      , required:       "This value is required"
      , pattern:        "The value has invalid characters"
      , min:            "This value should be greater than or equal to %s"
      , max:            "This value should be lower than or equal to %s"
      , range:          "A value between %s and %s is needed"
      , minlength:      "At least %s characters are needed"
      , maxlength:      "At most %s characters are allowed"
      , length:         "A value between %s and %s characters is needed"
      , mincheck:       "You must select at least %s choices"
      , maxcheck:       "You must select %s choices or less"
      , check:          "You must select between %s and %s choices"
      , equalto:        "This value should be the same."

      })

    })();

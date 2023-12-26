{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Admin change form JS

{%endcomment%}

{% load nested_admin %}


mp.admin_submit_form = function() {
    $("form").submit()
    {% if is_popup %}
        window.close()
    {% endif %}
    }

{% if change and not is_view_only %}

    {#-- Hide screen elements not visible for add or read only #}
    $('.mp_change_only').removeClass('mp_hidden')

    {#-- Setup image loads to occur immediately  #}
    mp.ajax_submit_form_images( '#{{ opts.model_name }}_form'
            {% if media_client_url %}, {{ media_client_url }}{% endif %}
            )

{% endif %}

{#-- Inject select2 lookup field handling #}

const autolookup_selects = {% get_json adminform.form 'autolookup_select_data' '[]' %}

{#-- Add lookup to inline-admin forms by replicating ID layout #}
{% for formset in inline_admin_formsets %}
    {% for form in formset.forms %}
        for( const field of {% get_json form 'autolookup_select_data' '[]' %} ) {
            field.name = '{{ formset.formset.prefix }}-{{ form|form_index }}-' +
                        field.name
            autolookup_selects.push( field )
            }
    {% endfor %}
{% endfor %}

_.each( autolookup_selects, function( field ) {
    setup_autolookup_field( field )
    })
function setup_autolookup_field( field ) {
    $( "#id_" + field.name )
        {#-- Create any existing items and trigger their selection #}
        .each( function() {
            const select2 = $(this)
            const init = field.init_value
            if( init ) {
                var option = new Option( init.name, init.id, true, true )
                select2.append( option ).trigger('change')
                select2.trigger({
                    type: 'select2:select',
                    params: { data: init }
                    })
                }
            })
        {#-- Setup select2 for all autolookup fields #}
        .select2({
            width: '100%',
            ajax: {
                url: mpurl.api_autolookup,
                dataType: 'json',
                delay: 250,
                data: function( params ) {
                    return {
                        search: params.term,
                        app: field.app,
                        model: field.model,
                        page: params.page,
                        }
                    },
                processResults: function( data ) {
                    return {
                        results: data,
                        }
                    },
                }
            })
    }

django.jQuery('.related-widget-wrapper select').trigger('change')

{#-- HACK - rearrange inlines #}
$('div.inline-group').each( function() {
    const placeholder = $( "fieldset.mp_placeholder." + $(this).attr("id") )
    if( placeholder.length ) {
        $( placeholder ).append( $(this) )
        }
    })

{#-- HACK - Copy fixup occurs when copy button pressed #}
mp.admin_copy_start_fixup = function() {
    {#-- Add querystring to indicate next screen is a copy #}
    $('#admin_main form').attr( 'action',
            location.pathname + '?mpf_admin_copy_save=1' )
    {#-- Support additions to default behavior #}
    if( mp.admin_copy_start_override ) {
        mp.admin_copy_start_override()
        }
    else {
        {#-- Try to update common fields #}
        const name = $("#id_name")
        if( name.length ) {
            $(".mp_admin_copymessage").text( "Copying " + _.trim( name.val() ) )
            name.val( 'Copy of ' + _.trim( name.val() ) )
            }
        }
    }

{#-- HACK - Copy redirects press copy button #}
{% if admin_copy_request %}
    $('#mpsavecopy').click()
{% endif %}

{#-- Don't let new copy screen copy #}
{% if admin_copy_new %}
    if( mp.admin_copy_new_override ) {
        mp.admin_copy_new_override()
        }
    $(".mp_admin_copy").hide()
    $(".mp_admin_history").hide()
    $(".mp_admin_cancel").hide()
{% endif %}

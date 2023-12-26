{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Shared admin tree scripting

{%endcomment%}


{#-- Put add itme menu with content item nested tabular #}
const add_item = $("tr.add-row > .djn-add-item")
add_item.find( $(".djn-add-handler")
    .html("Add existing item") )
    .addClass('mp_button_text')
add_item.append( $("#template_tree_change_add").html() )
mp.init_menus( ".mp_menu_admin", 'mp_menu_highlight' )

{% if change %}

    {#-- Setup autolookup on new item fields #}
    django.jQuery( document ).on( 'djnesting:added', function( event, inline, row ) {
        const field = {
            name: row.attr('id') + '-item',
            model: 'baseitem',
            app: 'mpcontent',
            }
        autolookup_selects.push( field )
        setup_autolookup_field( field )
        })

    {#-- Set workflow button #}
    $("#collection_set_workflow").click( function() {
        mp.fetch({
            url: '{% url 'tree_set_workflow' %}',
            method: 'POST',
            data: {
                'tree_id': '{{ original.pk }}',
                'workflow_level': $("#id_workflow").val()
                },
            finished: function( values ) {
                var count = values['update_count']
                var items = values['item_names']
                mp.dialog_open( "Workflow updated for: " + count + "<br>" + items )
                }
            })
        })

    {#-- Set sandboxes button #}
    $("#collection_set_sandboxes").click( function() {
        var sandbox_ids = []
        $("#id_sandboxes input").each( function() {
            this.checked && sandbox_ids.push( mp.safe_int( $(this).val() ) )
            });
        mp.fetch({
            url: '{% url 'tree_set_sandboxes' %}',
            method: 'POST',
            data: {
                'tree_id': '{{ original.pk }}',
                'sandbox_ids': JSON.stringify( sandbox_ids ),
                },
            finished: function( values ) {
                var count = values['update_count']
                var items = values['item_names']
                mp.dialog_open( "Sites updated for: " + count + "<br>" + items )
                }
            })
        })

    {% if user.is_root_staff %}

        {#-- Rebuild tree button #}
        $("#collection_rebuild").click( function() {
            mp.fetch({
                url: '{% url 'tree_rebuild' %}',
                method: 'POST',
                data: {
                    "tree_top_id": "{{ original.pk }}",
                    },
                finished: function( values ) {
                    mp.dialog_open( values['rebuilt'] ? "Tree fixed" : "Tree fix failed" )
                    }
                })
            })

    {% endif %}

{% endif %}

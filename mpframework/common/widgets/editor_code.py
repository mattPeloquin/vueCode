#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Codemirror editor widget
    Shared code for both the codemirror-only widget, and for codemirror
    init of the combined widget.
"""

from ..utils import json_dump
from ..utils.html_utils import textarea_px_from_attrs
from .editor import mpEditorBase


_script_html = '''
    $( textarea ).ready( function() {{

        // Fixed configuration options not changed by widget
        const options = _.extend( {{
            refresh: true,
            highlightSelectionMatches: true,
            matchTags: true,
            indentWithTabs: false,
            extraKeys: {{
                // Fix tabbing
                "Shift-Tab": "indentLess",
                "Tab": "indentMore",
                }},
            }}, {config} )

        // Turn textarea into codemirror editor
        cm = CodeMirror.fromTextArea( textarea, options )
        cm.setSize( "100%", {height} )
        $( cm.getWrapperElement() )
            .attr( "id", "{id}_codemirror" )
            .addClass("mp_hidden")

        // Force refresh if parent visibility toggled
        $( textarea ).closest(".mp_collapse").find(".mp_collapse_handler")
            .click( function(e) {{
                cm.refresh()
                }})

        // Keep text area in sync with CM editor
        cm.on( "change", function() {{ cm.save() }} )

        {script_standalone}
        }})
    '''
_script_standalone = '''

    // Show the editor since it doesn't need to be toggled
    $("#{id}_codemirror").toggleClass( 'mp_hidden', false )
    cm.refresh()

    '''

def code_editor_settings( kwargs=None ):
    # Overridable defaults for setting up the code editor
    kwargs = kwargs or {}
    return {
        'mode': kwargs.pop( 'mode', 'htmlmixed' ),
        'theme': kwargs.pop( 'theme', 'twilight' ),
        'lineNumbers': kwargs.pop( 'lineNumbers', True ),
        'lineWrapping': kwargs.pop( 'lineWrapping', True ),
        'smartIndent': kwargs.pop( 'smartIndent', True ),
        'scrollbarStyle': kwargs.pop( 'scrollbarStyle', 'simple' ),
        'indentUnit': kwargs.pop( 'indent', 4 ),
        }

def code_editor_scripting( attrs, config=code_editor_settings(),
                            script_standalone='' ):
    _width, height = textarea_px_from_attrs( attrs )
    return _script_html.format(
                id=attrs.get('id'),
                config=json_dump( config ),
                height=height,
                script_standalone=script_standalone,
                )

class CodeEditor( mpEditorBase ):
    """
    Widget class for code-only editing using editor control.
    Uses the Textarea as base element for CodeMirror for easy integration
    with Django textarea support.
    """

    def __init__( self, *args, **kwargs ):

        # Required settings passed to CodeMirror on creation
        self.settings = code_editor_settings( kwargs )

        super().__init__( *args, **kwargs )


    def render_editor( self, attrs, value, **kwargs ):
        """
        Add code scripting to render
        """

        # Read only may be set dynamically, so set before render
        self.settings.update({
            'readOnly': self.readonly,
            })

        script_standalone = _script_standalone.format( id=attrs.get('id') )
        kwargs['script'] = code_editor_scripting( attrs, self.settings,
                                                    script_standalone )

        return super().render_editor( attrs, value, **kwargs )

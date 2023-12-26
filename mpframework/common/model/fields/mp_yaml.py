#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support easy use of Yaml in Django form and model fields.

    Fields by default treat YAML text content as SafeNestedDicts,
    but can also return normal dicts based on safe_dict option.

    SECURE - Only YAML safe dump and load are used.
    MPF Yaml model fields support human-friendly
    viewing and editing with standard data types in admin.
    Complex types are not needed, and staff users could enter
    insecure YAML into admin fields.

    The CSafeLoader and CSafeDumper are used for performance, note
    libyaml-devel must be installed before PyYAML to activate these.
"""
import yaml
from django import forms
from django.conf import settings
from django.db import models

from ... import log
from ... import CHAR_LEN_DB_SEARCH
from ...utils import SafeNestedDict
from ...logging.timing import mpTiming

# Fallback if PyYaml support not present
try:
    from yaml import CSafeLoader as SafeLoader
    from yaml import CSafeDumper as SafeDumper
except:
    log.info("YAML C LOAD/DUMP NOT AVAILABLE")
    from yaml import SafeLoader
    from yaml import SafeDumper


class _YamlFormField( forms.CharField ):
    """
    Show YamlFields as Yaml in the Admin UI.
    Since this can be called whenever value is needed, cache result.
    The default is to use SafeNestedDict, but normal dicts can be
    used for data with dotted names or where SafeNestedDict isn't needed.
    """
    widget = forms.Textarea

    def __init__( self, *args, **kwargs ):
       self.value_cache = ( None, None )
       self.safe_dict = kwargs.pop( 'safe_dict', True )
       super().__init__( *args, **kwargs )

    def prepare_value( self, value ):
        """
        Show value in display as indented Yaml.
        """
        cached_value, yaml_result = self.value_cache
        if value and cached_value != value:
            yaml_result = _dump_yaml( value, self, default_flow_style=False )
            self.value_cache = ( value, yaml_result )
        return yaml_result

    def to_python( self, value ):
        """
        Convert Yaml to dict for validation and for use when setting form value.
        Let any exceptions propagate to force validation error.
        """
        return _validate_parse_yaml( value, self )

class YamlField( models.TextField ):
    """
    Model field for accessing YAML from DB as Python object

    YAML is edited as text by users and stored as text. It is then
    loaded into a Python object and can be saved back as YAML.
    Only dicts are supported, as goal is to store structured data
    or present user options without separate DB fields.

    Use directly in templates with dot notation; None returned for empties.
    Outside templates, dict gets or references can be used; if values
    don't exist an empty SafeNestedDict is returned

    FUTURE - yaml-dict conversion has some round-trip issues on string quoting for block text
    """

    def __init__( self, *args, **kwargs ):
        self.safe_dict = kwargs.pop( 'safe_dict', True )
        # Ensure a default max length
        kwargs['max_length'] = kwargs.get( 'max_length', CHAR_LEN_DB_SEARCH )
        super().__init__( *args, **kwargs )
        log.debug_on() and log.detail2("YamlField init (%s)", id(self))

    def deconstruct( self ):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def formfield( self, **kwargs ):
        kwargs['form_class'] = _YamlFormField
        kwargs['safe_dict'] = self.safe_dict
        return super().formfield( **kwargs )

    def from_db_value( self, value, *args ):
        return _safe_parse_yaml( value, self )

    def to_python( self, value ):
        """
        Convert Yaml to dict for validation and for use when setting form value.
        Let any exceptions propagate to force validation error.
        """
        return _validate_parse_yaml( value, self )

    def get_prep_value( self, value ):
        """
        Convert dict from SafeNestedDict into Yaml string for saving.
        """
        rv = _dump_yaml( value, self )
        return rv

    def get_default( self ):
        """
        Support calling .get() without defaults on an empty YamlField
        """
        return SafeNestedDict() if self.safe_dict else {}

def _validate_parse_yaml( yaml_text, obj ):
    """
    Throw validation error if problem converting Yaml
    """
    try:
        return _parse_yaml( yaml_text, obj )
    except Exception as e:
        log.info("CONFIG - Yaml input error: %s %s", type(e), e )
        raise forms.ValidationError(
                u"There is a problem with the YAML formatting"
                )

def _safe_parse_yaml( yaml_text, obj ):
    """
    Return an empty safe dict if problems in YAML conversion.
    """
    try:
        return _parse_yaml( yaml_text, obj )
    except Exception as e:
        log.info("CONFIG - YamlField load: %s %s -> %s, %s",
                    type(e), e, obj, str(yaml_text)[:80])
        if settings.MP_TESTING:
            raise
        return SafeNestedDict() if obj.safe_dict else {}

def _parse_yaml( yaml_text, obj ):
    """
    Convert dict or yaml string into SafeNestedDict object.
    Note this is called EVERY TIME a model is instantiated, so frequently
    used models may need to optimize use of potentially large YAML fields.
    Non-dict values are ignored.
    """
    rv = SafeNestedDict() if obj.safe_dict else {}
    if yaml_text:
        if log.debug_on():
            t = mpTiming()

        # Handle to_python semantics of already having an object
        # of the given type
        if isinstance( yaml_text, dict ):
            parsed_dict = yaml_text

        # Otherwise, load the string as Yaml
        else:
            parsed_dict = yaml.load( yaml_text, Loader=SafeLoader )

        rv.update( parsed_dict )

        if log.debug_on():
            log.db2("%s Yaml load %s: %s", t, obj, str(rv)[:120])
    return rv

def _dump_yaml( value, _obj, **kwargs ):
    """
    Convert dict into a Yaml sting
    Note saved as native dict, as pyYaml doesn't know how to save SafeNestedDict.
    """
    rv = ''
    if value:
        try:
            if isinstance( value, SafeNestedDict ):
                value = dict( value )
            if isinstance( value, dict ):
                rv = yaml.dump( value, Dumper=SafeDumper, **kwargs )
            else:
                # Handle bad YAML entered field, send back to form as string to fix
                rv = value
        except Exception as e:
            log.info("CONFIG - YamlField dump: %s %s -> %s, %s",
                        type(e), e, _obj, str(value)[:80])
            if settings.MP_TESTING:
                raise
        if log.debug_on():
            log.db2("Yaml dump %s, %s: %s -> %s, %s",
                    _obj, id(rv), str(value)[:120], type(rv), str(rv)[:120])
    return rv

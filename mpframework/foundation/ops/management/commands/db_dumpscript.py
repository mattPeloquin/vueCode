# -*- coding: UTF-8 -*-
"""
    MPF version of dumpscript that only does explicitly defined models
    in a specific order.

    PORTIONS ADAPTED FROM OPEN SOURCE:
      https://github.com/django-extensions/django-extensions
 """

import datetime
import sys
from optparse import make_option
from timezone_field import TimeZoneField

import six
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import (
    AutoField, BooleanField, DateField, DateTimeField, FileField, ForeignKey,
    )
from django_extensions.management.utils import signalcommand
from django.utils.encoding import smart_text, force_text

from mpframework.common import log

from mpframework.foundation.tenant.models.provider import Provider


def orm_item_locator(orm_obj):
    """
    This function is called every time an object that will not be exported is required.
    Where orm_obj is the referred object.
    We postpone the lookup to locate_object() which will be run on the generated script

    """

    the_class = orm_obj._meta.object_name
    original_class = the_class
    pk_name = orm_obj._meta.pk.name
    original_pk_name = pk_name
    pk_value = getattr(orm_obj, pk_name)

    while hasattr(pk_value, "_meta") and hasattr(pk_value._meta, "pk") and hasattr(pk_value._meta.pk, "name"):
        the_class = pk_value._meta.object_name
        pk_name = pk_value._meta.pk.name
        pk_value = getattr(pk_value, pk_name)

    clean_dict = make_clean_dict(orm_obj.__dict__)

    for key in clean_dict:
        v = clean_dict[key]
        if v is not None and not isinstance(v, (six.string_types, six.integer_types, float, datetime.datetime)):
            clean_dict[key] = six.u("%s" % v)

    output = """ importer.locate_object(%s, "%s", %s, "%s", %s, %s ) """ % (
        original_class, original_pk_name,
        the_class, pk_name, pk_value, clean_dict
    )
    return output


# A user-friendly file header
FILE_HEADER = """

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file has been automatically generated.
# Instead of changing it, create a file called import_helper.py
# and put there a class called ImportHelper(object) in it.
#
# This class will be specially casted so that instead of extending object,
# it will actually extend the class BasicImportHelper()
#
# That means you just have to overload the methods you want to
# change, leaving the other ones inteact.
#
#
# This file was generated with the following command:
# %s
#
# to restore it, run
# manage.py runscript module_name.this_script_name
#

from django.db import transaction

class BasicImportHelper(object):

    def pre_import(self):
        pass

    @transaction.atomic
    def run_import(self, import_data):
        import_data()

    def post_import(self):
        pass

    def locate_similar(self, current_object, search_data):
        # You will probably want to call this method from save_or_locate()
        # Example:
        #   new_obj = self.locate_similar(the_obj, {"national_id": the_obj.national_id } )

        the_obj = current_object.__class__.objects.get(**search_data)
        return the_obj

    def locate_object(self, original_class, original_pk_name, the_class, pk_name, pk_value, obj_content):
        # You may change this function to do specific lookup for specific objects
        #
        # original_class class of the django orm's object that needs to be located
        # original_pk_name the primary key of original_class
        # the_class      parent class of original_class which contains obj_content
        # pk_name        the primary key of original_class
        # pk_value       value of the primary_key
        # obj_content    content of the object which was not exported.
        #
        # You should use obj_content to locate the object on the target db
        #
        # An example where original_class and the_class are different is
        # when original_class is Farmer and the_class is Person. The table
        # may refer to a Farmer but you will actually need to locate Person
        # in order to instantiate that Farmer
        #
        # Example:
        #   if the_class == SurveyResultFormat or the_class == SurveyType or the_class == SurveyState:
        #       pk_name="name"
        #       pk_value=obj_content[pk_name]
        #   if the_class == StaffGroup:
        #       pk_value=8

        search_data = { pk_name: pk_value }
        the_obj = the_class.objects.get(**search_data)
        #print(the_obj)
        return the_obj


    def save_or_locate( self, the_obj):
        # Change this if you want to locate the object in the database
        try:
            the_obj.save()
        except:
            print("---------------")
            print("Error saving the following object:")
            print(the_obj.__class__)
            print(" ")
            print(the_obj.__dict__)
            print(" ")
            print(the_obj)
            print(" ")
            print("---------------")

            raise
        return the_obj


importer = None
try:
    import import_helper
    # We need this so ImportHelper can extend BasicImportHelper, although import_helper.py
    # has no knowlodge of this class
    importer = type("DynamicImportHelper", (import_helper.ImportHelper, BasicImportHelper ) , {} )()
except ImportError  as e:
    # From Python 3.3 we can check e.name - string match is for backward compatibility.
    if 'import_helper' in str(e):
        importer = BasicImportHelper()
    else:
        raise

import datetime
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType

try:
    import dateutil.parser
except ImportError:
    print("Please install python-dateutil")
    sys.exit(os.EX_USAGE)

def run():
    importer.pre_import()
    importer.run_import(import_data)
    importer.post_import()

def import_data():

""" % " ".join(sys.argv)


class Command( BaseCommand ):

    def add_arguments( self, parser ):

        parser.add_argument( '--pid', dest='pid',
                             default=None, help='Provider id to export' )
        parser.add_argument( '--exclude_field_list', dest='exclude_fields',
                             default=None, help='Fields to exclude' )
        parser.add_argument( '--fixup_list', dest='fixup_models',
                             default=None, help='Models to fixup' )

    help = 'Dumps provider data as a customised python script.'
    args = '[appname.model ...]'

    @signalcommand
    def handle( self, *models, **options ):

        models = get_models( models )

        # A dictionary is created to keep track of all the processed objects,
        # so that foreign key references can be made using python variable names.
        # This variable "context" will be passed around like the town bicycle.
        context = {}

        # Create a dumpscript object and let it format itself as a string
        script = Script(
            models=models,
            context=context,
            stdout=self.stdout,
            stderr=self.stderr,
            options=options,
            )

        self.stdout.write( str(script) )
        self.stdout.write("\n")


def get_models( app_labels ):
    """
    Get models either explicity or from apps
    """

    from django.db.models import get_app, get_apps, get_model
    from django.db.models import get_models as get_all_models

    # These models are not to be output, e.g. because they can be generated automatically
    # TODO: This should be "appname.modelname" string
    EXCLUDED_MODELS = (ContentType, )

    models = []

    # If no app labels are given, return all
    if not app_labels:
        for app in get_apps():
            models += [m for m in get_all_models(app) if m not in EXCLUDED_MODELS]
        return models

    # Get all relevant apps
    for app_label in app_labels:
        # If a specific model is mentioned, get only that model
        if "." in app_label:
            app_label, model_name = app_label.split(".", 1)
            models.append(get_model(app_label, model_name))
        # Get all models for a given app
        else:
            models += [m for m in get_all_models(get_app(app_label)) if m not in EXCLUDED_MODELS]

    log.debug("Models for: %s", ' '.join([ model.__name__ for model in models ]))

    return models


class Code:
    """
    This keeps track of import statements and can be output to a string.
    """

    def __init__(self, indent=-1, stdout=None, stderr=None):

        if not stdout:
            stdout = sys.stdout
        if not stderr:
            stderr = sys.stderr

        self.indent = indent
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        """ Returns a string representation of this script.
        """
        if self.imports:
            self.stderr.write(repr(self.import_lines))
            return flatten_blocks([""] + self.import_lines + [""] + self.lines, num_indents=self.indent)
        else:
            return flatten_blocks(self.lines, num_indents=self.indent)

    def get_import_lines(self):
        """ Takes the stored imports and converts them to lines
        """
        if self.imports:
            return ["from %s import %s" % (value, key) for key, value in self.imports.items()]
        else:
            return []
    import_lines = property(get_import_lines)


class ModelCode( Code ):
    """
    Produces a python script that can recreate data for a given model class.
    """

    def __init__(self, model, context=None, stdout=None, stderr=None, options=None):
        super().__init__(indent=0, stdout=stdout, stderr=stderr)
        self.model = model
        if context is None:
            context = {}
        self.context = context
        self.options = options
        self.instances = []

    def get_imports(self):
        """ Returns a dictionary of import statements, with the variable being
            defined as the key.
        """
        return {self.model.__name__: smart_text(self.model.__module__)}
    imports = property(get_imports)

    def get_lines(self):
        """ Returns a list of lists or strings, representing the code body.
            Each list is a block, each string is a statement.
        """
        code = []

        provider = Provider.objects.get( id=int(self.options['pid']) )

        for counter, item in enumerate( self.model.objects.filter( _provider=provider ) ):

            instance = InstanceCode( instance=item, count=counter + 1,
                                     context=self.context, stdout=self.stdout, stderr=self.stderr, options=self.options )
            self.instances.append(instance)
            if instance.waiting_list:
                code += instance.lines

        # After each instance has been processed, try again.
        # This allows self referencing fields to work.
        for instance in self.instances:
            if instance.waiting_list:
                code += instance.lines

        return code

    lines = property(get_lines)


class InstanceCode( Code ):
    """
    Produces a python script that can recreate data for a given model instance.
    """

    def __init__(self, instance, count, context=None, stdout=None, stderr=None, options=None):

        super().__init__(indent=0, stdout=stdout, stderr=stderr)
        self.imports = {}

        self.options = options
        self.instance = instance
        self.model = self.instance.__class__
        if context is None:
            context = {}
        self.context = context
        self.variable_name = "%s%s_%s" % (self.instance._meta.db_table, count, self.instance.pk)
        self.instantiated = False

        # FUTURE - convert dumpscript to use get_fields

        self.waiting_list = list(self.model._meta.fields)

        # Create lists of non-through MTM relationships to add
        self.many_to_many_waiting_list = {}
        for field in self.model._meta.many_to_many:
            if field.rel.through._meta.auto_created:
                self.many_to_many_waiting_list[ field ] = list( getattr( self.instance, field.name ).all() )


    def get_lines( self, force=False ):
        """
        Returns a list of lists or strings, representing the code body.
        Each list is a block, each string is a statement.

        force (True or False): if an attribute object cannot be included,
        it is usually skipped to be processed later. With 'force' set, there
        will be no waiting: a get_or_create() call is written instead.
        """
        code_lines = []

        # Initialise our new object
        # e.g. model_name_35 = Model()
        code_lines += self.instantiate()

        # Add each field
        # e.g. model_name_35.field_one = 1034.91
        #      model_name_35.field_two = "text"
        code_lines += self.get_waiting_list()

        if force:
            # TODO: Check that M2M are not affected
            code_lines += self.get_waiting_list(force=force)

        # Display the save command for new object, e.g. model_name_35.save()
        if code_lines:
            code_lines.append("%s = importer.save_or_locate(%s)\n" % (self.variable_name, self.variable_name))

        code_lines += self.get_many_to_many_lines( force=force )

        return code_lines

    lines = property( get_lines )


    def instantiate(self):
        " Write lines for instantiation "
        # e.g. model_name_35 = Model()
        code_lines = []

        if not self.instantiated:
            code_lines.append("%s = %s()" % (self.variable_name, self.model.__name__))
            self.instantiated = True

            # Store our variable name for future foreign key references
            pk_name = self.instance._meta.pk.name
            key = '%s_%s' % (self.model.__name__, getattr(self.instance, pk_name))
            self.context[key] = self.variable_name

        return code_lines


    def get_waiting_list( self, force=False ):
        """
        Add lines for any waiting fields that can be completed now.
        """
        code_lines = []

        exclude_fields = self.options.get( 'exclude_fields', [] )
        if isinstance( exclude_fields, str ):
            exclude_fields = eval( exclude_fields )

        # Process normal fields
        for field in list( self.waiting_list ):

            if field.name in exclude_fields:
                continue

            try:
                # Find the value, add the line, remove from waiting list and move on
                value = get_attribute_value( self.instance, field, self.context, force=force )
                code_lines.append('%s.%s = %s' % (self.variable_name, field.name, value))
                self.waiting_list.remove( field )

            except SkipValue:
                # Remove from the waiting list and move on
                self.waiting_list.remove( field )
                continue

            except DoLater:
                # Move on, maybe next time
                continue

        return code_lines


    def get_many_to_many_lines( self, force=False ):
        """
        Generates lines that define many to many relations for this instance.
        """
        lines = []

        for field, rel_items in self.many_to_many_waiting_list.items():
            for rel_item in list( rel_items ):
                try:
                    pk_name = rel_item._meta.pk.name
                    key = '%s_%s' % (rel_item.__class__.__name__, getattr(rel_item, pk_name))
                    value = "%s" % self.context[key]
                    lines.append('%s.%s.add(%s)' % (self.variable_name, field.name, value))
                    self.many_to_many_waiting_list[field].remove(rel_item)

                except KeyError:
                    if force:
                        item_locator = orm_item_locator(rel_item)
                        self.context["__extra_imports"][rel_item._meta.object_name] = rel_item.__module__
                        lines.append('%s.%s.add( %s )' % (self.variable_name, field.name, item_locator))
                        self.many_to_many_waiting_list[field].remove(rel_item)
        if lines:
            lines.append("")
        return lines


class Script( Code ):
    " Produces a complete python script that can recreate data for the given apps. "

    def __init__(self, models, context=None, stdout=None, stderr=None, options=None):
        super().__init__(stdout=stdout, stderr=stderr)
        self.imports = {}

        self.models = models
        if context is None:
            context = {}
        self.context = context

        self.context["__avaliable_models"] = set(models)
        self.context["__extra_imports"] = {}

        self.options = options


    def get_lines(self):
        """
        Returns a list of lists or strings, representing the code body.
        Each list is a block, each string is a statement.
        """
        code = [ FILE_HEADER.strip() ]

        # Queue and process the required models

        model_queue = []
        for model in self.models:
            model_class = ModelCode( model=model, context=self.context,
                              stdout=self.stdout, stderr=self.stderr, options=self.options )
            model_queue.append( model_class )

        for model_class in model_queue:
            msg = 'Processing model: %s' % model_class.model.__name__
            self.stderr.write( msg + "\n" )
            code.append( "    # " + msg + "\n")
            code.append( "    print '" + msg + "'" )
            code.append( model_class.import_lines )
            code.append("")
            code.append( model_class.lines )

        #
        # Process left over foreign keys from cyclic models
        #
        fixup_list = self.options.get( 'fixup_models', [] )
        if isinstance( fixup_list, str ):
            fixup_list = eval( fixup_list )
        fixup_models = get_models( fixup_list )
        for model in fixup_models:
            for model_class in model_queue:
                if model_class.model == model:
                    msg = 'Re-processing model: %s\n' % model_class.model.__name__
                    self.stderr.write( msg )
                    code.append("    # " + msg)
                    for instance in model_class.instances:
                        if instance.waiting_list or instance.many_to_many_waiting_list:
                            code.append( instance.get_lines(force=True) )


        code.insert(1, "    # Initial Imports")
        code.insert(2, "")
        for key, value in self.context["__extra_imports"].items():
            code.insert(2, "    from %s import %s" % (value, key))

        return code

    lines = property(get_lines)


    def _queue_models(self, models, context):
        """ Works an an appropriate ordering for the models.
            This isn't essential, but makes the script look nicer because
            more instances can be defined on their first try.
        """

        # Max number of cycles allowed before we call it an infinite loop.
        MAX_CYCLES = 20

        model_queue = []
        number_remaining_models = len(models)
        allowed_cycles = MAX_CYCLES

        while number_remaining_models > 0:
            previous_number_remaining_models = number_remaining_models

            model = models.pop(0)

            # If the model is ready to be processed, add it to the list
            if check_dependencies(model, model_queue, context["__avaliable_models"]):
                model_class = ModelCode(model=model, context=context, stdout=self.stdout, stderr=self.stderr, options=self.options)
                model_queue.append(model_class)

            # Otherwise put the model back at the end of the list
            else:
                models.append(model)

            # Check for infinite loops.
            # This means there is a cyclic foreign key structure
            # That cannot be resolved by re-ordering
            number_remaining_models = len(models)
            if number_remaining_models == previous_number_remaining_models:
                allowed_cycles -= 1
                if allowed_cycles <= 0:
                    # Add the remaining models, but do not remove them from the model list
                    missing_models = [ModelCode(model=m, context=context, stdout=self.stdout, stderr=self.stderr, options=self.options) for m in models]
                    model_queue += missing_models
                    # Replace the models with the model class objects
                    # (sure, this is a little bit of hackery)
                    models[:] = missing_models
                    break
            else:
                allowed_cycles = MAX_CYCLES

        return model_queue


# HELPER FUNCTIONS
#-------------------------------------------------------------------------------


def get_attribute_value( item, field, context, force=False ):
    """
    Gets a string version of the given attribute's value,
    """

    # Don't include the auto fields, they'll be automatically recreated
    if isinstance( field, AutoField ):
        raise SkipValue()

    # Find the value of the field, catching any database issues
    try:
        value = getattr(item, field.name)
    except ObjectDoesNotExist:
        raise SkipValue('Could not find object for %s.%s, ignoring.\n' % (item.__class__.__name__, field.name))

    # Some databases (eg MySQL) might store boolean values as 0/1, this needs to be cast as a bool
    if isinstance( field, BooleanField ) and value is not None:
        return repr( bool(value) )

    elif isinstance( field, FileField ):
        return repr( force_text(value) )

    # ForeignKey fields, link directly using our stored python variable name
    elif isinstance( field, ForeignKey ) and value is not None:

        # Special case for contenttype foreign keys: no need to output any
        # content types in this script, as they can be generated again
        # automatically.
        # NB: Not sure if "is" will always work
        if field.rel.to is ContentType:
            return 'ContentType.objects.get(app_label="%s", model="%s")' % (value.app_label, value.model)

        # Generate an identifier (key) for this foreign object
        pk_name = value._meta.pk.name
        key = '%s_%s' % (value.__class__.__name__, getattr(value, pk_name))

        if key in context:
            variable_name = context[key]
            # If the context value is set to None, this should be skipped.
            # This identifies models that have been skipped (inheritance)
            if variable_name is None:
                raise SkipValue()
            # Return the variable name listed in the context
            return "%s" % variable_name
        elif value.__class__ not in context["__avaliable_models"] or force:
            context["__extra_imports"][value._meta.object_name] = value.__module__
            item_locator = orm_item_locator(value)
            return item_locator
        else:
            raise DoLater('(FK) %s.%s\n' % (item.__class__.__name__, field.name))

    elif isinstance( field, (DateField, DateTimeField) ) and value is not None:
        return "dateutil.parser.parse(\"%s\")" % value.isoformat()

    # FUTURE HACK - figure out how TimeZoneField wants to be dumpted
    elif isinstance( field, (TimeZoneField) ) and value is not None:
        return "'UTC'"

    else:
        return repr( value )


def flatten_blocks(lines, num_indents=-1):
    """ Takes a list (block) or string (statement) and flattens it into a string
        with indentation.
    """

    # The standard indent is four spaces
    INDENTATION = " " * 4

    if not lines:
        return ""

    # If this is a string, add the indentation and finish here
    if isinstance(lines, six.string_types):
        return INDENTATION * num_indents + lines

    # If this is not a string, join the lines and recurse
    return "\n".join([flatten_blocks(line, num_indents + 1) for line in lines])


def make_clean_dict(the_dict):
    if "_state" in the_dict:
        clean_dict = the_dict.copy()
        del clean_dict["_state"]
        return clean_dict
    return the_dict


def check_dependencies(model, model_queue, avaliable_models):
    " Check that all the depenedencies for this model are already in the queue. "

    # A list of allowed links: existing fields, itself and the special case ContentType
    allowed_links = [m.model.__name__ for m in model_queue] + [model.__name__, 'ContentType']

    # For each ForeignKey or ManyToMany field, check that a link is possible

    for field in model._meta.fields:
        if field.rel and field.rel.to.__name__ not in allowed_links:
            if field.rel.to not in avaliable_models:
                continue
            return False

    for field in model._meta.many_to_many:
        if field.rel and field.rel.to.__name__ not in allowed_links:
            return False

    return True


# EXCEPTIONS
#-------------------------------------------------------------------------------

class SkipValue(Exception):
    """ Value could not be parsed or should simply be skipped. """


class DoLater(Exception):
    """ Value could not be parsed or should simply be skipped. """


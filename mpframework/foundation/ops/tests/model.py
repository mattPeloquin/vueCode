#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test for Ops models
"""
from django.db import models

from mpframework.common import log
from mpframework.common.tasks import mp_async
from mpframework.common.tasks import run_queue_function
from mpframework.common.tasks.tests import test_job
from mpframework.testing.framework import ModelTestCase

# This function must be module level to be loaded by async
@mp_async
def test_task( **kwargs ):
    log.info("TEST TASK: %s -> %s", kwargs['my_task'], kwargs['text'] )


class ModelTests( ModelTestCase ):

    def test_async( self ):
        """
        Use task/job test framework
        """
        self.l("Task permutations")
        for num in range(4):
            text = "task%s" % num
            run_queue_function( test_task, None, text=text, my_priority='HI' )
            run_queue_function( test_task, 'TASK_TEST', text=text, my_priority='HI', my_cache=None )
            run_queue_function( test_task, 'TASK_TEST', text=text, my_priority='HS' )
            run_queue_function( test_task, 'TASK_TEST', text=text, my_priority='HSU' )
            run_queue_function( test_task, 'TASK_TEST', text=text )
            run_queue_function( test_task, 'TASK_TEST', text=text, my_priority='MI' )
            run_queue_function( test_task, 'TASK_TEST', text=text, my_priority='MSU' )
            run_queue_function( test_task, 'TASK_TEST', text=text, my_priority='LS' )
        self.l("Run some jobs")
        test_job( "Test job", depth=1, tasks=30, jobs=0 )
        test_job( "Big test job", depth=4, tasks=4, jobs=4 )

        self.wait_for_threads()

    def test_general( self ):

        self.l("Test get_url_list")
        from mpframework.common.utils.http import get_url_list
        get_url_list()

        """
        HACK - To avoid messing around with special test models, test
        custom fields by appropriating uses in existing models
        """
        from mpframework.foundation.tenant.models.provider import Provider
        from mpframework.foundation.tenant.models.sandbox import Sandbox
        from mpframework.user.mpuser.models import mpUser

        provider = Provider.objects.get( pk=11 )
        s = Sandbox( _provider=provider, subdomain='newsand' )

        self.l("Yaml Field")
        test_list = ["item1", "item2"]
        _options = {
            'test_list': test_list,
            'nested': {
                'string': 'test string',
                'number': 3,
                }
            }
        s.options.update( _options )
        s.save()
        self.assertTrue( s.options['test_list'] == test_list )
        self.assertTrue( s.options['nested']['string'] == 'test string' )
        self.assertTrue( s.options['nested.string'] == 'test string' )
        self.assertTrue( s.options.get('nested.number') == 3 )
        self.assertTrue( s.options.get('nested').get('number') == 3 )
        self.assertFalse( s.options['bad'] )
        self.assertFalse( s.options['bad.bad']['bad'] )
        self.assertTrue( s.options.get('bad', 'test') == 'test' )
        self.assertTrue( s.options.get('bad.bad', 'test') == 'test' )

        self.l("Truncate CharField")
        u = mpUser.objects.create_obj( email="TestTrunFieldsUser", password=self.TEST_PWD,
                                       sandbox=s )
        u.notes = "Note Test"
        u.save()
        u.notes = "LongTestString" * 1000
        u.save()


#--------------------------------------------------------------------
# Test Support

class DummyTestModel( models.Model ):
    """
    Dummy model to allow self-contained testing against a model
    """
    dummy = models.CharField( max_length=20 )


def _mv( value, model ):
    """
    "Model Value"
    Return a value with the model id baked in, to ensure programmatic
    checks of model values are attached to the right models
    """
    if model is None:
        return value
    if isinstance( value, ( int, float ) ):
        return value + model.pk
    elif isinstance( value, list ):
        rv = list( value )
        rv.append( model.pk )
        return rv
    elif isinstance( value, dict ):
        rv = dict( value )
        rv.update( {'test': model.id} )
        return rv
    else:
        return "%s-%s" % (value, model.pk)

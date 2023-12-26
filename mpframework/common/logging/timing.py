#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support for capturing timing and debugging info during a
    request, for both debug and non-debug execution
"""
import operator
from functools import reduce

from .utils import db_queries


class mpTiming:
    """
    Timing interface assumes using seconds (as float)
    """

    def __init__( self, db=True ):
        from ..utils import ElapsedTime
        from ..utils import get_random_key
        self.timer = ElapsedTime()
        self.pk = get_random_key( 3 ).lower()

        # If doing DB tracking, note current state of connection queries
        # to subtract later
        self.db = {} if db else None
        if db:
            self.db['start_queries'], self.db['start_time'] = self.db_info()

    def __str__( self ):
        return self.log_row

    @property
    def total( self ):
        return self.timer.elapsed().total_seconds()

    @property
    def log_total( self ):
        return "{:.3f}s".format( self.total )

    def mark( self, checkpoint=None ):
        """
        Set checkpoint for returning recent seconds, for timing
        blocks of code with an existing timer
        """
        self.timer.set( checkpoint )

    def recent( self, checkpoint=None ):
        return self.timer.get( checkpoint ).total_seconds()

    def log_recent( self, checkpoint=None ):
        return "{:.3f}s".format( self.recent() )

    @property
    def log_row( self ):
        time = '{:.2f}s'.format( self.total ).lstrip('0')
        return '{}{}'.format( time, self.db_log() )

    def db_log( self ):
        """
        Return string with any DB info
        """
        rv = ''
        from ..log import info_on
        if self.db and info_on() > 1:
            queries, seconds = self.db_info()
            queries -= self.db['start_queries']
            if queries:
                if seconds:
                    seconds -= self.db['start_time']
                    elapsed = '-{:.2f}'.format( seconds ).lstrip('0').lstrip('.')
                else:
                    elapsed = ''
                rv = ' D{}{}'.format( queries, elapsed )
            else:
                rv = ' ND'
        return rv

    def db_info( self, do_time=True ):
        """
        Return numerical values for any DB information
        """
        queries = db_queries()
        time = False if not do_time else reduce( operator.add,
                            [ float(q.get('time')) for q in queries ],
                            0.0 )
        return len(queries), time


class mpTimingNone:
    def __init__( self, db=True ):
        self.pk = 'NO_RT'
    @property
    def log_row( self ):
        return ''
    @property
    def total( self ):
        return 0.0
    @property
    def log_total( self ):
        return ''
    def mark( self, _=None ):
        pass
    def recent( self ):
        return 0.0
    def log_recent( self ):
        return ''
    def db_info( self, _=True ):
        return 0, 0.0

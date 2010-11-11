"""Core event interfaces."""

from sqlalchemy import event, exc

class DDLEvents(event.Events):
    """
    Define create/drop event listers for schema objects.
    
    These events currently apply to :class:`.Table`
    and :class:`.MetaData` objects as targets.
    
    e.g.::
    
        from sqlalchemy import event
        from sqlalchemy import Table, Column, Metadata, Integer
        
        m = MetaData()
        some_table = Table('some_table', m, Column('data', Integer))
        
        def on_after_create(target, connection, **kw):
            connection.execute("ALTER TABLE %s SET name=foo_%s" % 
                                    (target.name, target.name))
                                    
        event.listen(on_after_create, "on_after_create", some_table)
    
    DDL events integrate closely with the 
    :class:`.DDL` class and the :class:`.DDLElement` hierarchy
    of DDL clause constructs, which are themselves appropriate 
    as listener callables::
    
        from sqlalchemy import DDL
        event.listen(
            DDL("ALTER TABLE %(table)s SET name=foo_%(table)s"),
            "on_after_create",
            some_table
        )
    
    The methods here define the name of an event as well
    as the names of members that are passed to listener
    functions.
    
    See also:

        :ref:`event_toplevel`
        
        :class:`.DDLElement`
        
        :class:`.DDL`
        
        :ref:`schema_ddl_sequences`
    
    """
    
    def on_before_create(self, target, connection, **kw):
        """ """

    def on_after_create(self, target, connection, **kw):
        """ """

    def on_before_drop(self, target, connection, **kw):
        """ """
    
    def on_after_drop(self, target, connection, **kw):
        """ """
    

class PoolEvents(event.Events):
    """Available events for :class:`.Pool`.
    
    The methods here define the name of an event as well
    as the names of members that are passed to listener
    functions.
    
    e.g.::
    
        from sqlalchemy import event
        
        def my_on_checkout(dbapi_conn, connection_rec, connection_proxy):
            "handle an on checkout event"
            
        events.listen(my_on_checkout, 'on_checkout', Pool)

    In addition to accepting the :class:`.Pool` class and :class:`.Pool` instances,
    :class:`.PoolEvents` also accepts :class:`.Engine` objects and
    the :class:`.Engine` class as targets, which will be resolved
    to the ``.pool`` attribute of the given engine or the :class:`.Pool`
    class::
        
        engine = create_engine("postgresql://scott:tiger@localhost/test")
        
        # will associate with engine.pool
        events.listen(my_on_checkout, 'on_checkout', engine)

    """
    
    @classmethod
    def accept_with(cls, target):
        from sqlalchemy.engine import Engine
        from sqlalchemy.pool import Pool
        
        if isinstance(target, type):
            if issubclass(target, Engine):
                return Pool
            elif issubclass(target, Pool):
                return target
        elif isinstance(target, Engine):
            return target.pool
        else:
            return target
    
    def on_connect(self, dbapi_connection, connection_record):
        """Called once for each new DB-API connection or Pool's ``creator()``.

        :param dbapi_con:
          A newly connected raw DB-API connection (not a SQLAlchemy
          ``Connection`` wrapper).

        :param con_record:
          The ``_ConnectionRecord`` that persistently manages the connection

        """

    def on_first_connect(self, dbapi_connection, connection_record):
        """Called exactly once for the first DB-API connection.

        :param dbapi_con:
          A newly connected raw DB-API connection (not a SQLAlchemy
          ``Connection`` wrapper).

        :param con_record:
          The ``_ConnectionRecord`` that persistently manages the connection

        """

    def on_checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Called when a connection is retrieved from the Pool.

        :param dbapi_con:
          A raw DB-API connection

        :param con_record:
          The ``_ConnectionRecord`` that persistently manages the connection

        :param con_proxy:
          The ``_ConnectionFairy`` which manages the connection for the span of
          the current checkout.

        If you raise an ``exc.DisconnectionError``, the current
        connection will be disposed and a fresh connection retrieved.
        Processing of all checkout listeners will abort and restart
        using the new connection.
        """

    def on_checkin(self, dbapi_connection, connection_record):
        """Called when a connection returns to the pool.

        Note that the connection may be closed, and may be None if the
        connection has been invalidated.  ``checkin`` will not be called
        for detached connections.  (They do not return to the pool.)

        :param dbapi_con:
          A raw DB-API connection

        :param con_record:
          The ``_ConnectionRecord`` that persistently manages the connection

        """

class EngineEvents(event.Events):
    """Available events for :class:`.Engine`.
    
    The methods here define the name of an event as well as the names of members that are passed to listener functions.
    
    e.g.::
    
        from sqlalchemy import event, create_engine
        
        def on_before_execute(conn, clauseelement, multiparams, params):
            log.info("Received statement: %s" % clauseelement)
        
        engine = create_engine('postgresql://scott:tiger@localhost/test')
        event.listen(on_before_execute, "on_before_execute", engine)
    
    Some events allow modifiers to the listen() function.
    
    :param retval=False: Applies to the :meth:`.on_before_execute` and 
      :meth:`.on_before_cursor_execute` events only.  When True, the
      user-defined event function must have a return value, which
      is a tuple of parameters that replace the given statement 
      and parameters.  See those methods for a description of
      specific return arguments.
    
    """
    
    @classmethod
    def listen(cls, fn, identifier, target, retval=False):
        from sqlalchemy.engine.base import Connection, \
            _listener_connection_cls
        if target.Connection is Connection:
            target.Connection = _listener_connection_cls(
                                        Connection, 
                                        target.dispatch)
        
        if not retval:
            if identifier == 'on_before_execute':
                orig_fn = fn
                def wrap(conn, clauseelement, multiparams, params):
                    orig_fn(conn, clauseelement, multiparams, params)
                    return clauseelement, multiparams, params
                fn = wrap
            elif identifier == 'on_before_cursor_execute':
                orig_fn = fn
                def wrap(conn, cursor, statement, 
                        parameters, context, executemany):
                    orig_fn(conn, cursor, statement, 
                        parameters, context, executemany)
                    return statement, parameters
                fn = wrap
                    
        elif retval and identifier not in ('on_before_execute', 'on_before_cursor_execute'):
            raise exc.ArgumentError(
                    "Only the 'on_before_execute' and "
                    "'on_before_cursor_execute' engine "
                    "event listeners accept the 'retval=True' "
                    "argument.")
        event.Events.listen(fn, identifier, target)

    def on_before_execute(self, conn, clauseelement, multiparams, params):
        """Intercept high level execute() events."""

    def on_after_execute(self, conn, clauseelement, multiparams, params, result):
        """Intercept high level execute() events."""
        
    def on_before_cursor_execute(self, conn, cursor, statement, 
                        parameters, context, executemany):
        """Intercept low-level cursor execute() events."""

    def on_after_cursor_execute(self, conn, cursor, statement, 
                        parameters, context, executemany):
        """Intercept low-level cursor execute() events."""

    def on_begin(self, conn):
        """Intercept begin() events."""
        
    def on_rollback(self, conn):
        """Intercept rollback() events."""
        
    def on_commit(self, conn):
        """Intercept commit() events."""
        
    def on_savepoint(self, conn, name=None):
        """Intercept savepoint() events."""
        
    def on_rollback_savepoint(self, conn, name, context):
        """Intercept rollback_savepoint() events."""
        
    def on_release_savepoint(self, conn, name, context):
        """Intercept release_savepoint() events."""
        
    def on_begin_twophase(self, conn, xid):
        """Intercept begin_twophase() events."""
        
    def on_prepare_twophase(self, conn, xid):
        """Intercept prepare_twophase() events."""
        
    def on_rollback_twophase(self, conn, xid, is_prepared):
        """Intercept rollback_twophase() events."""
        
    def on_commit_twophase(self, conn, xid, is_prepared):
        """Intercept commit_twophase() events."""


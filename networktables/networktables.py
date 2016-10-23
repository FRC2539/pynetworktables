
import threading

from ntcore.api import NtCoreApi

import logging
logger = logging.getLogger('nt')

__all__ = ["NetworkTables"]


class NetworkTables:
    """
    This is the global singleton that you use to initialize NetworkTables
    connections, configure global settings and listeners, and to create
    NetworkTable instances which can be used to send data to/from
    NetworkTable servers and clients.
    
    First, you must initialize NetworkTables::
    
        from networktables import NetworkTables
    
        # As a client to connect to a robot
        NetworkTables.initialize(server='roborio-XXX-frc.local')
    

    Then, to interact with the SmartDashboard you get an instance of the
    table, and you can call the various methods

        
        sd = NetworkTables.getTable('SmartDashboard')

        sd.putNumber('someNumber', 1234)
        otherNumber = sd.getNumber('otherNumber')
        ...
        
    .. seealso::
    
        The examples in the documentation.
        
        :class:`.NetworkTable`
    """
    
    #: The path separator for sub-tables and keys
    PATH_SEPARATOR = '/'
    #: The default port that network tables operates on
    DEFAULT_PORT = 1735
    
    #_queuedAutoUpdateValues = []
    #_autoListener = AutoUpdateListener()
    
    _persistentFilename = None
    
    port = DEFAULT_PORT
    ipAddress = None
    
    _mode = 'server'
    _running = False
    _tables = {}

    _staticMutex = threading.RLock()

    _api = NtCoreApi()

    @classmethod
    def _checkInit(cls):
        with cls._staticMutex:
            if cls._running:
                raise RuntimeError("Network tables has already been initialized")

    @classmethod
    def initialize(cls, server=None):
        """Initializes NetworkTables and begins operations
        
        :param server: If specified, NetworkTables will be set to client
                       mode and attempt to connect to the specified server.
                       This is equivalent to executing::
                       
                           cls.setIPAddress(server)
                           cls.setClientMode()
                           cls.initialize()
        
        .. versionadded:: 2017.0.0
           The *server* and *verbose* parameters
        """
        
        with cls._staticMutex:
            cls._checkInit()
            
            if server is not None:
                cls._mode = 'client'
                cls.ipAddress = server
            
            if cls._mode == 'server':
                cls._api.startServer(cls._persistentFilename, "", cls.port)
            elif cls._mode == 'client':
                cls._api.startClient([(cls.ipAddress, cls.port)])
            elif cls._mode == 'dashboard':
                raise ValueError("Dashboard mode isn't implemented yet")
            elif cls._mode == 'test':
                pass
            else:
                raise ValueError("Invalid NetworkTables mode '%s'" % cls._mode)

            from networktables import __version__
            logger.info("NetworkTables %s initialized in %s mode",
                        __version__, cls._mode)

            cls._running = True
            
            # TODO
            #if cls._queuedAutoUpdateValues:
            #    q = cls._queuedAutoUpdateValues
            #    cls._queuedAutoUpdateValues = None
            #    for args in q:
            #        cls.getGlobalAutoUpdateValue(*args)    
    
    @classmethod
    def shutdown(cls):
        """
        .. versionadded:: 2017.0.0
        """
        
        with cls._staticMutex:
            
            if not cls._running:
                return
            
            try:
                if cls._mode in ['client', 'dashboard']:
                    cls._api.stopClient()
                elif cls._mode == 'server':
                    cls._api.stopServer()
            finally:
                cls._running = False
                cls._persistentFilename = None
                cls._mode = 'server'
                cls._tables = {}
                cls.port = cls.DEFAULT_PORT
                cls.ipAddress = None
                cls._api = NtCoreApi()
    
    @classmethod
    def setClientMode(cls):
        """Set that network tables should be a client
        
        .. warning:: This must be called before :meth:`initalize` or :meth:`getTable`
        """
        with cls._staticMutex:
            cls._checkInit()
            cls._mode = 'client'
            
    @classmethod
    def setServerMode(cls):
        """set that network tables should be a server (this is the default)
        
        .. warning:: This must be called before :meth:`initalize` or :meth:`getTable`
        """
        with cls._staticMutex:
            cls._checkInit()
            cls._mode = 'server'
    
    @classmethod
    def setTeam(cls, team):
        """set the team the robot is configured for (this will set the ip
        address that network tables will connect to in client mode)
        
        :param team: the team number
        
        .. warning:: This must be called before :meth:`initalize` or :meth:`getTable`
        """
        cls.setIPAddress('roboRIO-%d-FRC.local' % team)

    @classmethod
    def setIPAddress(cls, address):
        """:param address: the adress that network tables will connect to in
            client mode
        
        .. warning:: This must be called before :meth:`initalize` or :meth:`getTable`
        """
        with cls._staticMutex:
            cls._checkInit()
            cls.ipAddress = address
    
    @classmethod
    def setPort(cls, port):
        """Sets the port number that network tables will connect to in
        client mode or listen to in server mode.
        
        :param port: the port number 
        
        .. versionadded:: 2017.0.0
        """
        with cls._staticMutex:
            cls._checkInit()
            cls.port = port
    
    @classmethod
    def setPersistentFilename(cls, filename):
        """Sets the persistent filename. Not used on the client.
         
        :param filename: the filename that the network tables server uses for
                         automatic loading and saving of persistent values
                         
        .. versionadded:: 2017.0.0
        """
        
        with cls._staticMutex:
            cls._checkInit()
            cls._persistentFilename = filename
        
    
    @classmethod
    def setNetworkIdentity(cls, name):
        """Sets the network identity. This is provided in the connection info
        on the remote end.
        
        .. versionadded:: 2017.0.0
        """
        cls._api.setNetworkIdentity(name)
        
    @classmethod
    def globalDeleteAll(cls):
        """Deletes ALL keys in ALL subtables.
        
        .. warn:: Use with caution!
        
        .. versionadded:: 2017.0.0
        """
        cls._api.globalDeleteAll()
    
    @classmethod
    def flush(cls):
        """Flushes all updated values immediately to the network.
     
        .. note:: This is rate-limited to protect the network from flooding.
                  This is primarily useful for synchronizing network updates
                  with user code.
        
        .. versionadded:: 2017.0.0
        """
        cls._api.flush()
    
    @classmethod
    def setUpdateRate(cls, interval):
        """Sets the period of time between writes to the network. 
        
        WPILib's networktables and SmartDashboard default to 100ms, we have
        set it to 50ms instead for quicker response time. You should not set
        this value too low, as it could potentially increase the volume of
        data sent over the network.
        
        .. warning:: If you don't know what this setting affects, don't mess
                     with it!
        
        :param interval: Write flush period in seconds (default is 0.050,
                         or 50ms)
                        
        .. versionadded:: 2017.0.0
        """
        cls._api.setUpdateRate(interval)

    # Deprecated alias
    setWriteFlushPeriod = setUpdateRate
    
    @classmethod
    def savePersistent(cls, filename):
        """Saves persistent keys to a file.  The server does this automatically.
        
        .. versionadded:: 2017.0.0
        """
        return cls._api.savePersistent(filename)
        
    @classmethod
    def loadPersistent(cls, filename):
        """Loads persistent keys from a file.  The server does this automatically.
        
        .. versionadded:: 2017.0.0
        """
        return cls._api.loadPersistent(filename)
    
    
    @classmethod
    def setDashboardMode(cls):
        """This will allow the driver station to connect to your code and
        receive the IP address of the robot from it. You must not call
        :meth:`setClientMode`, :meth:`setTeam`, or :meth:`setIPAddress`
        
        .. warning:: Only use this if your pynetworktables client is running
                     on the same host as the driver station, or nothing will
                     happen! 
                     
                     This mode will only connect to the robot if the FRC
                     Driver Station is able to connect to the robot and the
                     LabVIEW dashboard has been disabled.
        
        .. warning:: This must be called before :meth:`initalize` or :meth:`getTable`
        """
        with cls._staticMutex:
            cls._checkInit()
            cls._mode = 'dashboard'
            
    @classmethod
    def setTestMode(cls):
        """Setup network tables to run in unit test mode
        
        .. warning:: This must be called before :meth:`initalize` or :meth:`getTable`
        """
        with cls._staticMutex:
            cls._checkInit()
            cls._mode = 'test'
            
    @classmethod
    def enableVerboseLogging(cls):
        """Enable verbose logging that can be useful when trying to diagnose
        NetworkTables issues.
        
        .. warn:: Don't enable this in normal use, as it can potentially 
                  cause performance issues due to the volume of logging.
                  
        .. versionadded:: 2017.0.0
        """
        with cls._staticMutex:
            cls._checkInit()
            cls._api.setVerboseLogging(True)
    
    @classmethod
    def getTable(cls, key):
        """Gets the table with the specified key. If the table does not exist,
        a new table will be created.

        This will automatically initialize network tables if it has not been
        already initialized.

        :param key: the key name
        :returns: the network table requested
        :rtype: :class:`.NetworkTable`
        """
        with cls._staticMutex:
            if not cls._running:
                cls.initialize()
            
            if len(key) == 0 or key.startswith(cls.PATH_SEPARATOR):
                path = key
            else:
                path = cls.PATH_SEPARATOR + key
            
            table = cls._tables.get(path)
            if table is not None:
                return table
            
            # TODO: circular import problem, fix in 2018
            from .networktable import NetworkTable
                
            table = NetworkTable(path, cls._api)
            cls._tables[path] = table
            return table

    @classmethod
    def getGlobalTable(cls):
        """Returns an object that allows you to write values to raw network table
        keys (which are paths with / separators).

        This will automatically initialize network tables if it has not been
        already.

        .. note:: This is now an alias for ``NetworkTables.getTable('')``
        
        .. versionadded:: 2015.2.0
        .. versionchanged:: 2017.0.0
           Returns a NetworkTable instance

        :rtype: :class:`.NetworkTable`
        """
        return cls.getTable('')
        

    @classmethod
    def addGlobalListener(cls, listener, immediateNotify=True):
        '''Adds a listener that will be notified when any key in any
        NetworkTable is changed. The keys that are received using this
        listener will be full NetworkTable keys. Most users will not
        want to use this listener type.

        The listener is called from the NetworkTables I/O thread, and should
        return as quickly as possible.

        This will automatically initialize network tables if it has not been
        already.

        :param listener: A callable that has this signature: `callable(key, value, isNew)`
        :param immediateNotify: If True, the listener will be called immediately with the current values of the table

        .. versionadded:: 2015.2.0

        .. warning:: You may call the NetworkTables API from within the
                     listener, but it is not recommended as we are not
                     currently sure if deadlocks will occur
        '''
        with cls._staticMutex:
            if cls._staticProvider is None:
                cls.initialize()
            cls._staticProvider.addGlobalListener(listener, immediateNotify)

    @classmethod
    def removeGlobalListener(cls, listener):
        '''Removes a global listener

        .. versionadded:: 2015.2.0
        '''
        with cls._staticMutex:
            cls._staticProvider.removeGlobalListener(listener)
            
    @classmethod
    def getGlobalAutoUpdateValue(cls, key, defaultValue, writeDefault):
        '''Global version of getAutoUpdateValue. This function will not initialize
        NetworkTables.
        
        .. versionadded:: 2015.3.0
        '''
        with cls._staticMutex:
            
            autoListener = cls._autoListener
            
            if cls._staticProvider is None:
                cls._queuedAutoUpdateValues.append((key, defaultValue, writeDefault))
                gtable = None
            else:
                # initialize auto listener if not already done
                autoListener.init()
                gtable = cls._staticProvider.getNode()
        
        value = defaultValue
        
        if gtable:
            if writeDefault:
                gtable.putValue(key, value)
            else:
                try:
                    value = gtable.getValue(key)
                except KeyError:
                    gtable.putValue(key, value)
        
        return autoListener.createAutoValue(key, value)


    @classmethod
    def getRemoteAddress(cls):
        '''
            Only returns a valid address if connected to the server. If
            this is a server, returns None
            
            :returns: IP address of server or None
            
            .. versionadded:: 2015.3.2
        '''
        return cls._api.getRemoteAddress()

    @classmethod
    def isConnected(cls):
        """
            :returns: True if connected to at least one other NetworkTables
                      instance
        """
        return cls._api.getIsConnected()

    @classmethod
    def isServer(cls):
        """:returns: True if configured in server mode"""
        return cls._mode == 'server'
    
    @classmethod
    def addConnectionListener(cls, listener, immediateNotify=False):
        '''Adds a listener that will be notified when a new connection to a 
        NetworkTables client/server is established.
        
        The listener is called from a NetworkTables owned thread and should
        return as quickly as possible.
        
        :param listener: A function that will be called with two parameters
        :type listener: fn(bool, ConnectionInfo)
        
        :param immediateNotify: If True, the listener will be called immediately
                                with any active connection information
        
        .. warning:: You may call the NetworkTables API from within the
                     listener, but it is not recommended.
                     
        .. versionchanged:: 2017.0.0
           The listener is now a function
        '''
        assert callable(listener)
        cls._api.addConnectionListener(listener, immediateNotify)

    @classmethod
    def removeConnectionListener(cls, listener):
        '''Removes a connection listener
        
        :param listener: The function registered for connection notifications
        '''
        cls._api.removeConnectionListener(listener)



import threading

__all__ = ["NetworkTable"]

# TODO: in 2018, remove this circular import
from .networktables import NetworkTables as _NT

from ntcore.constants import (
    NT_BOOLEAN,
    NT_DOUBLE,
    NT_STRING,
    NT_RAW,
    NT_BOOLEAN_ARRAY,
    NT_DOUBLE_ARRAY,
    NT_STRING_ARRAY,
    
    NT_PERSISTENT
)

from ntcore.support.compat import stringtype
from ntcore.value import Value

class _defaultValueSentry:
    pass

class NetworkTable:
    '''
        This is a NetworkTable instance, it allows you to interact with
        NetworkTables in a table-based manner. You should not directly
        create a NetworkTable object, but instead use
        :meth:`.NetworkTables.getTable` to retrieve a NetworkTable instance.
        
        For example, to interact with the SmartDashboard::

            from networktables import NetworkTables
            sd = NetworkTables.getTable('SmartDashboard')
    
            sd.putNumber('someNumber', 1234)
            ...
            
        .. seealso::
    
            The examples in the documentation.
            
            :class:`.NetworkTables`
    '''
    
    PATH_SEPARATOR = '/'
    
    # These static aliases are deprecated and will be removed in 2018!
    
    initialize = _NT.initialize
    shutdown = _NT.shutdown
    setClientMode = _NT.setClientMode
    setServerMode = _NT.setServerMode
    setTeam = _NT.setTeam
    setIPAddress = _NT.setIPAddress
    setPort = _NT.setPort
    setPersistentFilename = _NT.setPersistentFilename
    setNetworkIdentity = _NT.setNetworkIdentity
    globalDeleteAll = _NT.globalDeleteAll
    flush = _NT.flush
    setUpdateRate = _NT.setUpdateRate
    setWriteFlushPeriod = _NT.setWriteFlushPeriod
    savePersistent = _NT.savePersistent
    loadPersistent = _NT.loadPersistent
    setDashboardMode = _NT.setDashboardMode
    setTestMode = _NT.setTestMode
    getTable = _NT.getTable
    getGlobalTable = _NT.getGlobalTable
    addGlobalListener = _NT.addGlobalListener
    removeGlobalListener = _NT.removeGlobalListener
    getGlobalAutoUpdateValue = _NT.getGlobalAutoUpdateValue
    
    addConnectionListener = _NT.addConnectionListener
    removeConnectionListener = _NT.removeConnectionListener
    
    getRemoteAddress = _NT.getRemoteAddress
    isConnected = _NT.isConnected
    isServer = _NT.isServer
    
    
    def __init__(self, path, api):
        self.path = path
        self._path = path + self.PATH_SEPARATOR
        self._api = api
        
        self.listenerMap = {}

    def __str__(self):
        return "NetworkTable: "+self.path
    
    def __repr__(self):
        return "<NetworkTable path=%s>" % self.path
    

    def addTableListener(self, listener, immediateNotify=False, key=None):
        '''Adds a listener that will be notified when any key in this
        NetworkTable is changed, or when a specified key changes.
        
        The listener is called from the NetworkTables I/O thread, and should
        return as quickly as possible.
        
        :param listener: A callable that has this signature: `callable(source, key, value, isNew)`
        :param immediateNotify: If True, the listener will be called immediately with the current values of the table
        :param key: If specified, the listener will only be called when this key is changed
        
        
        .. warning:: You may call the NetworkTables API from within the
                     listener, but it is not recommended as we are not
                     currently sure if deadlocks will occur
        '''
        adapters = self.listenerMap.setdefault(listener, [])
        if key is not None:
            adapter = NetworkTableKeyListenerAdapter(
                    key, self._path + key, self, listener)
        else:
            adapter = NetworkTableListenerAdapter(
                    self._path+self.PATH_SEPARATOR, self, listener)
        adapters.append(adapter)
        self.node.addTableListener(adapter, immediateNotify)

    def addSubTableListener(self, listener):
        '''Adds a listener that will be notified when any key in a subtable of
        this NetworkTable is changed.
        
        The listener is called from the NetworkTables I/O thread, and should
        return as quickly as possible.
        
        :param listener: A callable that has this signature: `callable(source, key, value, isNew)`
        
        .. warning:: You may call the NetworkTables API from within the
                     listener, but it is not recommended as we are not
                     currently sure if deadlocks will occur
        '''
        adapters = self.listenerMap.setdefault(listener, [])
        adapter = NetworkTableSubListenerAdapter(self._path, self, listener)
        adapters.append(adapter)
        self.node.addTableListener(adapter, True)

    def removeTableListener(self, listener):
        '''Removes a table listener
        
        :param listener: callable that was passed to :meth:`addTableListener`
                         or :meth:`addSubTableListener`
        '''
        adapters = self.listenerMap.get(listener)
        if adapters is not None:
            for adapter in adapters:
                self.node.removeTableListener(adapter)
            del adapters[:]

    def getSubTable(self, key):
        """Returns the table at the specified key. If there is no table at the
        specified key, it will create a new table

        :param key: the key name
        :returns: the networktable to be returned
        :rtype: :class:`NetworkTable`
        """
        path = self._path + key
        # TODO: cache these?
        return NetworkTable(path, self._api)
        

    def containsKey(self, key):
        """Determines whether the given key is in this table.
        
        :param key: the key to search for
        :returns: true if the table as a value assigned to the given key
        """
        path = self._path + key
        return self._api.getEntryValue(path) is not None

    def __contains__(self, key):
        return self.containsKey(key)

    def containsSubTable(self, key):
        """Determines whether there exists a non-empty subtable for this key
        in this table.
        
        :param key: the key to search for
        :returns: true if there is a subtable with the key which contains at least
        one key/subtable of its own
        """
        path = self._path + key + self.PATH_SEPARATOR
        return len(self._api.getEntryInfo(path, 0)) > 0
    
    def getKeys(self, types=0):
        """:param types: bitmask of types; 0 is treated as a "don't care".
        :returns: keys currently in the table
        
        .. versionadded:: 2017.0.0
        """
        keys = []
        for entry in self._api.getEntryInfo(self._path, types):
            relative_key = entry.name[len(self._path):]
            if self.PATH_SEPARATOR in relative_key:
                continue
            
            keys.append(relative_key)
        
        return keys
        
    def getSubTables(self):
        """:returns: subtables currently in the table
        
        .. versionadded:: 2017.0.0
        """
        keys = set()
        for entry in self._api.getEntryInfo(self._path, 0):
            relative_key = entry.name[len(self._path):]
            subst = relative_key.split(self.PATH_SEPARATOR)
            if len(subst) == 1:
                continue
            
            keys.add(subst[0])
        
        return keys
    
    def setPersistent(self, key):
        """Makes a key's value persistent through program restarts.
        
        :param key: the key to make persistent
        
        .. versionadded:: 2017.0.0
        """
        self.setFlags(key, NT_PERSISTENT)
        
    def clearPersistent(self, key):
        """Stop making a key's value persistent through program restarts.
        The key cannot be null.
        
        :param key: the key name
        
        .. versionadded:: 2017.0.0
        """
        self.clearFlags(key, NT_PERSISTENT)
    
    def isPersistent(self, key):
        """Returns whether the value is persistent through program restarts.
        The key cannot be null.
        
        :param key: the key name
        
        .. versionadded:: 2017.0.0
        """
        return self.getFlags(key) & NT_PERSISTENT != 0
        
    def delete(self, key):
        """Deletes the specified key in this table.
        
        :param key: the key name
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        self._api.deleteEntry(path)
    
    def setFlags(self, key, flags):
        """Sets flags on the specified key in this table. The key can
        not be null.
        
        :param key: the key name
        :param flags: the flags to set (bitmask)
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        self._api.setEntryFlags(path, self._api.getEntryFlags(path) | flags)
        
    def clearFlags(self, key, flags):
        """Clears flags on the specified key in this table. The key can
        not be null.
        
        :param key: the key name
        :param flags: the flags to clear (bitmask)
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        self._api.setEntryFlags(path, self._api.getEntryFlags(path) & ~flags)
        
    def getFlags(self, key):
        """Returns the flags for the specified key.
        
        :param key: the key name
        :returns: the flags, or 0 if the key is not defined
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.getEntryFlags(path)

    def putNumber(self, key, value):
        """Put a number in the table
        
        :param key: the key to be assigned to
        :param value: the value that will be assigned
        :returns: False if the table key already exists with a different type
        """
        path = self._path + key
        return self._api.setEntryValue(path, Value.makeDouble(value))

    def setDefaultNumber(self, key, defaultValue):
        """Gets the current value in the table, setting it if it does not exist.
        
        :param key: the key
        :param defaultValue: the default value to set if key doesn't exist.
        :returns: False if the table key exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setDefaultEntryValue(path, Value.makeDouble(defaultValue))

    def getNumber(self, key, defaultValue=_defaultValueSentry):
        """Gets the number associated with the given name.
        
        :param key: the key to look up
        :param defaultValue: the value to be returned if no value is found
        
        :returns: the value associated with the given key or the given default value
        if there is no value associated with the key
        
        :raises KeyError: If the value doesn't exist and no default is provided, or
                          if it is the wrong type
        """
        path = self._path + key
        value = self._api.getEntryValue(path)
        if not value or value.type != NT_DOUBLE:
            if defaultValue != _defaultValueSentry:
                return defaultValue
            raise KeyError(path)

        return value.value

    def putString(self, key, value):
        """Put a string in the table
        
        :param key: the key to be assigned to
        :param value: the value that will be assigned
        :returns: False if the table key already exists with a different type
        """
        path = self._path + key
        return self._api.setEntryValue(path, Value.makeString(value))

    def setDefaultString(self, key, defaultValue):
        """Gets the current value in the table, setting it if it does not exist.
        
        :param key: the key
        :param defaultValue: the default value to set if key doesn't exist.
        :returns: False if the table key exists with a different type
        """
        path = self._path + key
        return self._api.setDefaultEntryValue(path, Value.makeString(defaultValue))

    def getString(self, key, defaultValue=_defaultValueSentry):
        """Gets the string associated with the given name. If the key does not
        exist or is of different type, it will return the default value.
        
        :param key: the key to look up
        :param defaultValue: the value to be returned if no value is found
        :returns: the value associated with the given key or the given default value
        if there is no value associated with the key
        
        :raises KeyError: If the value doesn't exist and no default is provided, or
                          if it is the wrong type
        """
        path = self._path + key
        value = self._api.getEntryValue(path)
        if not value or value.type != NT_STRING:
            if defaultValue != _defaultValueSentry:
                return defaultValue
            raise KeyError(path)

        return value.value

    def putBoolean(self, key, value):
        """Put a boolean in the table
        
        :param key: the key to be assigned to
        :param value: the value that will be assigned
        :returns: False if the table key already exists with a different type
        """
        path = self._path + key
        return self._api.setEntryValue(path, Value.makeBoolean(value))

    def setDefaultBoolean(self, key, defaultValue):
        """Gets the current value in the table, setting it if it does not exist.
        
        :param key: the key
        :param defaultValue: the default value to set if key doesn't exist.
        :returns: False if the table key exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setDefaultEntryValue(path, Value.makeBoolean(defaultValue))

    def getBoolean(self, key, defaultValue=_defaultValueSentry):
        """Gets the boolean associated with the given name. If the key does not
         exist or is of different type, it will return the default value.

        :param key: the key name
        :param defaultValue: the default value if the key is None.  If not
                             specified, raises KeyError if the key is None.
        :returns: the key
        
        :raises KeyError: If the value doesn't exist and no default is provided, or
                          if it is the wrong type
        """
        path = self._path + key
        value = self._api.getEntryValue(path)
        if not value or value.type != NT_BOOLEAN:
            if defaultValue != _defaultValueSentry:
                return defaultValue
            raise KeyError(path)

        return value.value

    def putBooleanArray(self, key, value):
        """Put a boolean array in the table
        
        :param key: the key to be assigned to
        :param value: the value that will be assigned
        :returns: False if the table key already exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setEntryValue(path, Value.makeBooleanArray(value))
    
    def setDefaultBooleanArray(self, key, defaultValue=_defaultValueSentry):
        """Gets the current value in the table, setting it if it does not exist.
        
        :param key: the key
        :param defaultValue: the default value to set if key doesn't exist.
        :returns: False if the table key exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setDefaultEntryValue(path, Value.makeBooleanArray(defaultValue))
        
    def getBooleanArray(self, key, defaultValue=_defaultValueSentry):
        """Returns the boolean array the key maps to. If the key does not exist or is
        of different type, it will return the default value.
        
        :param key: the key to look up
        :param defaultValue: the value to be returned if no value is found
        :returns: the value associated with the given key or the given default value
        if there is no value associated with the key
        
        :raises KeyError: If the value doesn't exist and no default is provided, or
                          if it is the wrong type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        value = self._api.getEntryValue(path)
        if not value or value.type != NT_BOOLEAN_ARRAY:
            if defaultValue != _defaultValueSentry:
                return defaultValue
            raise KeyError(path)

        return value.value
    
    def putNumberArray(self, key, value):
        """Put a number array in the table
        :param key: the key to be assigned to
        :param value: the value that will be assigned
        :returns: False if the table key already exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setEntryValue(path, Value.makeDoubleArray(value))
    
    def setDefaultNumberArray(self, key, defaultValue):
        """Gets the current value in the table, setting it if it does not exist.
        
        :param key: the key
        :param defaultValue: the default value to set if key doesn't exist.
        :returns: False if the table key exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setDefaultEntryValue(path, Value.makeDoubleArray(defaultValue))
    
    def getNumberArray(self, key, defaultValue=_defaultValueSentry):
        """Returns the number array the key maps to. If the key does not exist or is
        of different type, it will return the default value.
        
        :param key: the key to look up
        :param defaultValue: the value to be returned if no value is found
        :returns: the value associated with the given key or the given default value
        if there is no value associated with the key
        
        :raises KeyError: If the value doesn't exist and no default is provided, or
                          if it is the wrong type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        value = self._api.getEntryValue(path)
        if not value or value.type != NT_DOUBLE_ARRAY:
            if defaultValue != _defaultValueSentry:
                return defaultValue
            raise KeyError(path)

        return value.value
        
    def putStringArray(self, key, value):
        """Put a string array in the table
        
        :param key: the key to be assigned to
        :param value: the value that will be assigned
        :returns: False if the table key already exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setEntryValue(path, Value.makeStringArray(value))
    
    def setDefaultStringArray(self, key, defaultValue):
        """Gets the current value in the table, setting it if it does not exist.
        
        :param key: the key
        :param defaultValue: the default value to set if key doesn't exist.
        :returns: False if the table key exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setDefaultEntryValue(path, Value.makeStringArray(defaultValue))
    
    def getStringArray(self, key, defaultValue=_defaultValueSentry):
        """Returns the string array the key maps to. If the key does not exist or is
        of different type, it will return the default value.
        
        :param key: the key to look up
        :param defaultValue: the value to be returned if no value is found
        :returns: the value associated with the given key or the given default value
        if there is no value associated with the key
        
        :raises KeyError: If the value doesn't exist and no default is provided, or
                          if it is the wrong type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        value = self._api.getEntryValue(path)
        if not value or value.type != NT_STRING_ARRAY:
            if defaultValue != _defaultValueSentry:
                return defaultValue
            raise KeyError(path)

        return value.value
        
    def putRaw(self, key, value):
        """Put a raw value (byte array) in the table
        :param key: the key to be assigned to
        :param value: the value that will be assigned
        :returns: False if the table key already exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setEntryValue(path, Value.makeRaw(value))
        
    def setDefaultRaw(self, key, defaultValue):
        """Gets the current value in the table, setting it if it does not exist.
        :param key: the key
        :param defaultValue: the default value to set if key doesn't exist.
        :returns: False if the table key exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        return self._api.setDefaultEntryValue(path, Value.makeRaw(defaultValue))
    
    def getRaw(self, key, defaultValue=_defaultValueSentry):
        """Returns the raw value (byte array) the key maps to. If the key does not
        exist or is of different type, it will return the default value.
        :param key: the key to look up
        :param defaultValue: the value to be returned if no value is found
        :returns: the value associated with the given key or the given default value
        if there is no value associated with the key
        
        :raises KeyError: If the value doesn't exist and no default is provided, or
                          if it is the wrong type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        value = self._api.getEntryValue(path)
        if not value or value.type != NT_RAW:
            if defaultValue != _defaultValueSentry:
                return defaultValue
            raise KeyError(path)

        return value.value
    
    def putValue(self, key, value):
        """Put a value in the table
        
        :param key: the key to be assigned to
        :param value: the value that will be assigned
        :returns: False if the table key already exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        if isinstance(value, bool):
            value = Value.makeBoolean(value)
        elif isinstance(value, (int, float)):
            value = Value.makeDouble(value)
        elif isinstance(value, stringtype):
            value = Value.makeString(value)
        
        else:
            raise ValueError("Can only put bool/int/str/bytes or iterable of those")
        
        path = self._path + key
        return self._api.setEntryValue(path, value)

    def setDefaultValue(self, key, defaultValue):
        """Gets the current value in the table, setting it if it does not exist.
        :param key: the key
        :param defaultValue: the default value to set if key doesn't exist.
        :returns: False if the table key exists with a different type
        
        .. versionadded:: 2017.0.0
        """
        
        path = self._path + key
        return self._api.setDefaultEntryValue(path, value)

    def getValue(self, key, defaultValue=_defaultValueSentry):
        """Gets the value associated with a key as an object
        
        :param key: the key of the value to look up
        :returns: the value associated with the given key
        
        :raises KeyError: If the value doesn't exist and no default is provided, or
                          if it is the wrong type
        
        .. versionadded:: 2017.0.0
        """
        path = self._path + key
        value = self._api.getEntryValue(path)
        if not value:
            if defaultValue != _defaultValueSentry:
                return defaultValue
            raise KeyError(path)

        return value.value
    
    def getAutoUpdateValue(self, key, defaultValue, writeDefault=True):
        '''Returns an object that will be automatically updated when the
        value is updated by networktables.
        
        .. note:: Does not work with complex types. If you modify the
                  returned type, the value will NOT be written back to
                  NetworkTables.
        
        :param key: the key name
        :type  key: str
        :param defaultValue: Default value to use if not in the table
        :type  defaultValue: any
        :param writeDefault: If True, put the default value to the table,
                             overwriting existing values
        :type  writeDefault: bool
        
        :rtype: :class:`.AutoUpdateValue`
        
        .. seealso:: :func:`.ntproperty` is a better alternative to use
        
        .. versionadded:: 2015.1.3
        '''
        return NetworkTable.getGlobalAutoUpdateValue(self._path + key, defaultValue, writeDefault)

    

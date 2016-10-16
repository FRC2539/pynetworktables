

class AutoUpdateValue:
    """Holds a value from NetworkTables, and changes it as new entries
    come in. Updates to this value are NOT passed on to NetworkTables.
    
    Do not create this object directly, as it only holds the value. 
    Use :meth:`.NetworkTable.getAutoUpdateValue` to obtain an instance
    of this.
    """
    
    __slots__ = ['key', '__value']
    
    def __init__(self, key, default):
        self.key = key
        self.__value = default
        
    def get(self):
        '''Returns the value held by this object'''
        return self.__value
    
    @property
    def value(self):
        return self.__value
    
    # Comparison operators et al
    
    def __lt__(self, other):
        raise TypeError("< not allowed on AutoUpdateValue objects. Use the .value attribute instead")
    def __le__(self, other):
        raise TypeError("<= not allowed on AutoUpdateValue objects. Use the .value attribute instead")
    def __eq__(self, other):
        raise TypeError("== not allowed on AutoUpdateValue objects. Use the .value attribute instead")
    def __ne__(self, other):
        raise TypeError("!= not allowed on AutoUpdateValue objects. Use the .value attribute instead")
    def __gt__(self, other):
        raise TypeError("> not allowed on AutoUpdateValue objects. Use the .value attribute instead")
    def __ge__(self, other):
        raise TypeError(">= not allowed on AutoUpdateValue objects. Use the .value attribute instead")
    
    def __bool__(self):
        raise TypeError("< not allowed on AutoUpdateValue objects. Use the .value attribute instead")
    
    def __hash__(self):
        raise TypeError("__hash__ not allowed on AutoUpdateValue objects")
    
    def __repr__(self):
        return '<AutoUpdateValue: %s>' % (self.__value.__repr__(), )

class AutoUpdateListener:
    
    def __init__(self):
        # no lock required if we use atomic operations (setdefault, get) on it
        self.keys = {}
        self.hasListener = False
        
    def init(self):
        if not self.hasListener:
            NetworkTable.addGlobalListener(self._valueChanged, False)
            self.hasListener = True
        
    def createAutoValue(self, key, default):
        new_value = AutoUpdateValue(key, default)
        return self.keys.setdefault(key, new_value)
    
    def _valueChanged(self, key, value, isNew):
        auto_value = self.keys.get(key)
        if auto_value is not None:
            auto_value._AutoUpdateValue__value = value


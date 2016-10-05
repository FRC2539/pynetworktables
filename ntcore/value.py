'''
    Internal storage for ntcore values
    
    Uses namedtuple for efficiency, and because Value objects are supposed
    to be immutable. Will have to measure that and see if there's a performance
    penalty for this in python.
    
    Original ntcore stores the last change time, but it doesn't seem to
    be used anywhere, so we don't store that to make equality comparison
    more efficient.
'''


from collections import namedtuple
from .structs import (
    NT_BOOLEAN,
    NT_DOUBLE,
    NT_STRING,
    NT_RAW,
    NT_BOOLEAN_ARRAY,
    NT_DOUBLE_ARRAY,
    NT_STRING_ARRAY,
    NT_RPC,
)

ValueType = namedtuple('Value', ['type', 'value'])


# optimization
_TRUE_VALUE = ValueType(NT_BOOLEAN, True)
_FALSE_VALUE = ValueType(NT_BOOLEAN, False)


class Value(object):
    
    @staticmethod
    def makeBoolean(value):
        if value:
            return _TRUE_VALUE
        else:
            return _FALSE_VALUE
        
    @staticmethod
    def makeDouble(value):
        return ValueType(NT_DOUBLE, value)

    @staticmethod
    def makeString(value):
        return ValueType(NT_STRING, value)
    
    @staticmethod
    def makeRaw(value):
        return ValueType(NT_RAW, value)
    
    # TODO: array stuff a good idea?
    
    @staticmethod
    def makeBooleanArray(value):
        return ValueType(NT_BOOLEAN_ARRAY, tuple(value))
    
    @staticmethod
    def makeDoubleArray(value):
        return ValueType(NT_DOUBLE_ARRAY, tuple(value))
    
    @staticmethod
    def makeStringArray(value):
        return ValueType(NT_STRING_ARRAY, tuple(value))

    @staticmethod
    def makeRpc(value):
        return ValueType(NT_RPC, value)
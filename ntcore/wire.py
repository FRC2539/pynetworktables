'''
    This encompasses the WireEncoder and WireDecoder stuff in ntcore
    
    Reading:
    
    Writing:
    
        Each message type will have a write function, which takes
        a single list argument. Bytes will be added to that list.
    
        The write routines assume that the messages are a tuple
        that have the following format:
        
            # This doesn't make sense
            type, str, value, id, flags, seqnum
    
'''

import struct

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
 
from .support import leb128

kKeepAlive =        b'\x00'
kClientHello =      b'\x01'
kProtoUnsup =       b'\x02'
kServerHelloDone =  b'\x03'
kServerHello =      b'\x04'
kClientHelloDone =  b'\x05'
kEntryAssign =      b'\x10'
kEntryUpdate =      b'\x11'
kFlagsUpdate =      b'\x12'
kEntryDelete =      b'\x13'
kClearEntries =     b'\x14'
kExecuteRpc =       b'\x20'
kRpcResponse =      b'\x21'


_bool_fmt = struct.Struct('?')
_double_fmt = struct.Struct('>d')
_string_fmt = struct.Struct('>H')
_array_fmt = struct.Struct('b')

_short_fmt = struct.Struct('>H')


def write_value_v2(v, out):
    out.append(v.type)
    if v.type == NT_BOOLEAN:
        out.append(_bool_fmt.pack(v.value))
        
    elif v.type == NT_DOUBLE:
        out.append(_double_fmt.pack(v.value))
        
    elif v.type == NT_STRING:
        s = v.value.encode('utf-8')
        out += (_string_fmt.pack(min(len(s), 0xffff)), s[:0xffff])
        
    elif v.type == NT_BOOLEAN_ARRAY:
        out.append(_array_fmt.pack(min(len(v.value), 0xff)))
        out += (_bool_fmt.pack(v) for v in v.value[:0xff])
        
    elif v.type == NT_DOUBLE_ARRAY:
        out.append(_array_fmt.pack(min(len(v.value), 0xff)))
        out += (_double_fmt.pack(v) for v in v.value[:0xff])
        
    elif v.type == NT_STRING_ARRAY:
        out.append(_array_fmt.pack(min(len(v.value), 0xff)))
        for s in v.value[:0xff]:
            s = v.value.encode('utf-8')
            out += (_string_fmt.pack(min(len(s), 0xffff)), s[:0xffff])
        
    else:
        raise ValueError("Invalid value type %s" % v)
    
# problem: need to read values now too. Same business.
    

def write_value_v3(v, out):
    out.append(v.type)
    if v.type == NT_BOOLEAN:
        out.append(_bool_fmt.pack(v.value))
        
    elif v.type == NT_DOUBLE:
        out.append(_double_fmt.pack(v.value))
        
    elif v.type in (NT_STRING, NT_RPC):
        s = v.value.encode('utf-8')
        out += (leb128.encode_uleb128(len(s)), s)
        
    elif v.type == NT_RAW:
        s = v.value
        out += (leb128.encode_uleb128(len(s)), s)
        
    elif v.type == NT_BOOLEAN_ARRAY:
        out.append(_array_fmt.pack(min(len(v.value), 0xff)))
        out += (_bool_fmt.pack(v) for v in v.value[:0xff])
        
    elif v.type == NT_DOUBLE_ARRAY:
        out.append(_array_fmt.pack(min(len(v.value), 0xff)))
        out += (_double_fmt.pack(v) for v in v.value[:0xff])
        
    elif v.type == NT_STRING_ARRAY:
        out.append(_array_fmt.pack(min(len(v.value), 0xff)))
        for s in v.value[:0xff]:
            s = v.value.encode('utf-8')
            out += (leb128.encode_uleb128(len(s)), s)
        
    else:
        raise ValueError("Invalid value type %s" % v)

    # basically the same thing
    
    # .. except string is uleb


class EmptyWireMessage(object):
        
    def write(self, msg, out):
        out.append(self.HEADER)
    
    def read(self):
        pass
    
    
class WireMessage(object):
    
    def __init__(self, STRUCT):
        self.STRUCT = struct.Struct(STRUCT)

    def write(self, msg, out):
        out += (self.HEADER,
                self.STRUCT.pack(*msg))

class WireMessageWithStringV3(object):
    
    def __init__(self, STRUCT):
        self.STRUCT = struct.Struct(STRUCT)

    def write(self, msg, out):
        out += (self.HEADER,
                self.STRUCT.pack(*msg),
                leb128.encode_uleb128(len(msg.str)),
                msg.str)     

class WireEntryAssignV2(object):
    pass

class WireEntryAssignV3(object):
    pass


class WireEntryUpdateV2(object):
    pass
class WireEntryUpdateV3(object):
    pass


V2_MAPPING = {
    kKeepAlive:       EmptyWireMessage(),
    kClientHello:     WireMessage('>H'),
    kProtoUnsup:      WireMessage('>H'),
    kServerHelloDone: EmptyWireMessage(),
    kServerHello:     WireEntryAssignV2('>bHH'),
    kEntryUpdate:     WireEntryUpdateV2('>HH'),
}

V3_MAPPING = {
    kKeepAlive:       EmptyWireMessage(),
    kClientHello:     WireMessageWithStringV3('>H'),
    kProtoUnsup:      WireMessage('>H'),
    kServerHelloDone: EmptyWireMessage(),
    kServerHello:     WireMessageWithStringV3('b'),
    kClientHelloDone: EmptyWireMessage(),
    kEntryAssign:     WireEntryAssignV3('>bHHb'),
    kEntryUpdate:     WireEntryUpdateV3('>HHb'),
    kFlagsUpdate:     WireMessage('>Hb'),
    kEntryDelete:     WireMessage('>H'),
    kClearEntries:    WireMessage('>I'),
    kExecuteRpc:      WireMessageWithStringV3('>HH'),
    kRpcResponse:     WireMessageWithStringV3('>HH'),
}

# fixup the headers

for k,v in V2_MAPPING.items():
    v.HEADER = k

for k,v in V3_MAPPING.items():
    v.HEADER = k
    




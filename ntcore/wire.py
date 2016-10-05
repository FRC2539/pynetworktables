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

import array
import struct

#from .structs import 
from .support import leb128
from ntcore.structs import NT_BOOLEAN_ARRAY, NT_STRING_ARRAY

bool_fmt = 'b?'
number_fmt = '>bd'

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
    
    def __init__(self, HEADER):
        self.HEADER = HEADER
        
    def write(self, msg, out):
        out.append(self.HEADER)
    
    #def read(self):
    #    pass
    
    
class WireMessage(object):
    
    def __init__(self, HEADER, STRUCT):
        self.HEADER = HEADER
        self.STRUCT = struct.Struct(STRUCT)

    def write(self, msg, out):
        out += (self.HEADER,
                self.STRUCT.pack(*msg))

class WireMessageWithStringV3(object):
    
    def __init__(self, HEADER, STRUCT):
        self.HEADER = HEADER
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



V2_KEEP_ALIVE =             EmptyWireMessage(b'\x00')
V2_CLIENT_HELLO =           WireMessage(b'\x01', '>H')
V2_PROTOCOL_UNSUPPORTED =   WireMessage(b'\x02', '>H')
V2_SERVER_HELLO_COMPLETE =  EmptyWireMessage(b'\x03')
V2_ENTRY_ASSIGNMENT =       WireEntryAssignV2(b'\x10', '>bHH')
V2_FIELD_UPDATE =           WireMessage(b'\x11', '>HH')


V3_KEEP_ALIVE =             EmptyWireMessage(b'\x00')
V3_CLIENT_HELLO =           WireMessageWithStringV3(b'\x01', '>H')
V3_PROTOCOL_UNSUPPORTED =   WireMessage(b'\x02', '>H')
V3_SERVER_HELLO_COMPLETE =  EmptyWireMessage(b'\x03')
V3_SERVER_HELLO =           WireMessageWithStringV3(b'\x04', 'b')
V3_CLIENT_HELLO_COMPLETE =  EmptyWireMessage(b'\x05')
V3_ENTRY_ASSIGNMENT =       WireEntryAssignV3(b'\x10', '>bHHb')
V3_FIELD_UPDATE =           WireMessage(b'\x11', '>HHb')
V3_FLAGS_UPDATE =           WireMessage(b'\x12', '>Hb')
V3_ENTRY_DELETE =           WireMessage(b'\x13', '>H')
V3_CLEAR_ENTRIES =          WireMessage(b'\x14', '>I')
V3_EXECUTE_RPC =            WireMessageWithStringV3(b'\x20', '>HH')
V3_RPC_RESPONSE =           WireMessageWithStringV3(b'\x21', '>HH')




V2_MAPPING = {}
V3_MAPPING = {}

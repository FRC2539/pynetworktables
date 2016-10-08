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
from .support.compat import range

from .constants import (
    NT_BOOLEAN,
    NT_DOUBLE,
    NT_STRING,
    NT_RAW,
    NT_BOOLEAN_ARRAY,
    NT_DOUBLE_ARRAY,
    NT_STRING_ARRAY,
    NT_RPC,
    
    kKeepAlive,
    kClientHello,
    kProtoUnsup,
    kServerHello,
    kServerHelloDone,
    kClientHelloDone,
    kEntryAssign,
    kEntryUpdate,
    kFlagsUpdate,
    kEntryDelete,
    kClearEntries,
    kExecuteRpc,
    kRpcResponse
)

from .support import leb128
from .value import Value


_bool_fmt = struct.Struct('?')
_double_fmt = struct.Struct('>d')
_string_fmt = struct.Struct('>H')
_array_fmt = struct.Struct('b')

_short_fmt = struct.Struct('>H')


class WireCodec(object):
    
    def __init__(self, proto_rev):
        self.set_proto_rev(proto_rev)
        
    def set_proto_rev(self, proto_rev):
        self.proto_rev = proto_rev
        if proto_rev == 0x0200:
            self.read_arraylen = self.read_arraylen_v2
            self.read_string = self.read_string_v2
            self.write_arraylen = self.write_arraylen_v2
            self.write_string = self.write_string_v2
            self.codecs = V2_MAPPING
            
        elif proto_rev == 0x0300:
            self.read_arraylen = self.read_arraylen_v3
            self.read_string = self.read_string_v3
            self.write_arraylen = self.write_arraylen_v3
            self.write_string = self.write_string_v3
            self.codecs = V3_MAPPING
        
        else:
            raise ValueError("Unsupported protocol")

    # This model would work if every message was the same.

    #def read(self, rstream):
    #    # read byte
    #    msgtype = rstream.read(1)
    #    
    #    m = self.codecs.get(msgtype)
    #    if m:
    #        return m.read(rstream)
    #    
    #    raise ValueError("Unrecognized message type '%s'" % msgtype)

    #def write(self, msg, out):
    #    codec = self.codecs.get(msg.type)
    #    if not codec:
    #        raise ValueError("Invalid message type %s for protocol %04x" % (msg.type, self.proto_rev))
    #    
    #    codec.write(msg, out)
    
    def read_value(self, vtype, rstream):
        if vtype == NT_BOOLEAN:
            return Value.makeBoolean(rstream.readStruct(_bool_fmt)[0])
        
        elif vtype == NT_DOUBLE:
            return Value.makeDouble(rstream.readStruct(_double_fmt)[0])
        
        elif vtype == NT_STRING:
            return Value.makeString(self.read_string(rstream))
        
        elif vtype == NT_BOOLEAN_ARRAY:
            alen = self.read_arraylen(rstream)
            return Value.makeBooleanArray([rstream.readStruct(_bool_fmt)[0] for _ in range(alen)])
        
        elif vtype == NT_DOUBLE_ARRAY:
            alen = self.read_arraylen(rstream)
            return Value.makeDoubleArray([rstream.readStruct(_double_fmt)[0] for _ in range(alen)])
        
        elif vtype == NT_STRING_ARRAY:
            alen = self.read_arraylen(rstream)
            return Value.makeStringArray([self.read_string(rstream) for _ in range(alen)])
        
        elif self.proto_rev >= 0x0300:
            if vtype == NT_RAW:
                slen = leb128.read_uleb128(rstream) 
                return Value.makeRaw(rstream.read(slen))
            
            elif vtype == NT_RPC:
                return Value.makeRpc(self.read_string(rstream))
        
        raise ValueError("Cannot decode value type %s" % vtype)
    
    def write_value(self, v, out):
        vtype = v.type
        out.append(vtype)
    
        if vtype == NT_BOOLEAN:
            out.append(_bool_fmt.pack(v.value))
            return
            
        elif vtype == NT_DOUBLE:
            out.append(_double_fmt.pack(v.value))
            return
            
        elif vtype == NT_STRING:
            self.write_string(v.value, out)
            return
            
        elif vtype == NT_BOOLEAN_ARRAY:
            alen = self.write_arraylen(v.value, out)
            out += (_bool_fmt.pack(v) for v in v.value[:alen])
            return
            
        elif vtype == NT_DOUBLE_ARRAY:
            alen = self.write_arraylen(v.value, out)
            out += (_double_fmt.pack(v) for v in v.value[:alen])
            return
            
        elif vtype == NT_STRING_ARRAY:
            alen = self.write_arraylen(v.value, out)
            for s in v.value[:alen]:
                self.write_string(s, out)
            return
                
        elif self.proto_rev >= 0x0300:
            if vtype == NT_RPC:
                self.write_string(v.value, out)
                return
            
            elif vtype == NT_RAW:
                s = v.value
                out += (leb128.encode_uleb128(len(s)), s)
                return
        
        raise ValueError("Cannot encode invalid value type %s" % vtype)
    
    
    #
    # v2/v3 routines
    #
    
    def read_arraylen_v2(self, rstream):
        return rstream.readStruct(_array_fmt)[0]
    
    def read_arraylen_v3(self, rstream):
        return leb128.read_uleb128(rstream) 
    
    def read_string_v2(self, rstream):
        slen = rstream.readStruct(_string_fmt)[0]
        return rstream.read(slen).decode('utf-8')
    
    def read_string_v3(self, rstream):
        slen = leb128.read_uleb128(rstream)
        return rstream.read(slen).decode('utf-8')
    
    
    def write_arraylen_v2(self, a, out):
        alen = min(len(a), 0xff)
        out.append(_array_fmt.pack(alen))
        return alen
    
    def write_arraylen_v3(self, a, out):
        alen = len(a)
        out.append(leb128.encode_uleb128(alen))
        return alen
    
    def write_string_v2(self, s, out):
        s = s.encode('utf-8')
        out += (_string_fmt.pack(min(len(s), 0xffff)), s[:0xffff])
    
    def write_string_v3(self, s, out):
        s = s.encode('utf-8')
        out += (leb128.encode_uleb128(len(s)), s)
        
    
    


#
# This is annoying. The wire message needs to know what type of
# thing to return, so that it can return a message
#
# I guess.. it could return an appropriately sized tuple?
#

# Ok, types are one to one. No doubt.



# encode, decode, transcode.. code
# .. 

class EmptyCodec(object):
    
    def write(self, msg, out):
        out.append(self.HEADER)
    
    # This should never be called...
    #def read(self):
    #    pass

    # writes a 0x0200
    
    # writes a 0x0300
    
    # .. this is silly

    
class StructCodec(object):
    
    def __init__(self, struct_fmt):
        self.STRUCT = struct.Struct(struct_fmt)
        
    def read(self, rstream):
        args = rstream.readStruct(self.STRUCT)
        return self.msgtype(self.type, *args)

    def write(self, msg, out):
        out += (self.HEADER,
                self.STRUCT.pack(*msg[1:]))


class ClientHelloCodec(object):
    pass

    # this sucks
    # read struct
    
    # if proto rev >= 0x0300
        # read string
    # else
        # string is None
        
    # return message

class WireMessageWithStringV3(object):
    
    def __init__(self, struct_fmt):
        self.STRUCT = struct.Struct(struct_fmt)
        
    def read(self, rstream):
        # header already nommed
        # how do I know the type. I guess... 
        
        # read the struct first
        args = rstream.readStruct(self.STRUCT)
        
        # read the string next
        msg_str = self.read_string(rstream)
        
        return self.msgtype(self.type, msg_str, *args)

    def write(self, msg, out):
        out += (self.type,
                self.STRUCT.pack(*(msg[2:])))
        self.write_string(msg.str, out)

class WireEntryAssignV2(StructCodec):
    pass

class WireEntryAssignV3(StructCodec):
    pass

    # read struct
    
    # the read value
    
    # create instance [easy, I know the type can only be one thing]


class WireEntryUpdateV2(StructCodec):
    pass

    # read function needs to ask for the entry type in
    # order to read the value.

class WireEntryUpdateV3(StructCodec):
    pass

    # value type is encoded here


V2_MAPPING = {
    kKeepAlive:       EmptyCodec(),
    kClientHello:     StructCodec('>H'),
    kProtoUnsup:      StructCodec('>H'),
    kServerHelloDone: EmptyCodec(),
    kEntryAssign:     WireEntryAssignV2('>bHH'),
    kEntryUpdate:     WireEntryUpdateV2('>HH'),
}

V3_MAPPING = {
    kKeepAlive:       EmptyCodec(),
    kClientHello:     WireMessageWithStringV3('>H'),
    kProtoUnsup:      StructCodec('>H'),
    kServerHelloDone: EmptyCodec(),
    kServerHello:     WireMessageWithStringV3('b'),
    kClientHelloDone: EmptyCodec(),
    kEntryAssign:     WireEntryAssignV3('>bHHb'),
    kEntryUpdate:     WireEntryUpdateV3('>HHb'),
    kFlagsUpdate:     StructCodec('>Hb'),
    kEntryDelete:     StructCodec('>H'),
    kClearEntries:    StructCodec('>I'),
    kExecuteRpc:      WireMessageWithStringV3('>HH'),
    kRpcResponse:     WireMessageWithStringV3('>HH'),
}

# fixup the headers

for k,v in V2_MAPPING.items():
    v.type = k

for k,v in V3_MAPPING.items():
    v.type = k


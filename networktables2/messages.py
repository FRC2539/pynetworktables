
import struct

__all__ = ["BadMessageError", "PROTOCOL_REVISION",
           "KEEP_ALIVE", "CLIENT_HELLO", "PROTOCOL_UNSUPPORTED",
           "SERVER_HELLO_COMPLETE", "ENTRY_ASSIGNMENT", "FIELD_UPDATE"]

# The definitions of all of the protocol message types

class BadMessageError(IOError):
    pass

PROTOCOL_REVISION = 0x0200

class Message:
    def __init__(self, HEADER, STRUCT=None):
        self.HEADER = HEADER
        if STRUCT is None:
            self.STRUCT = None
        else:
            self.STRUCT = struct.Struct(STRUCT)

    def getBytes(self, *args):
        b = bytearray(self.HEADER)
        if self.STRUCT is not None:
            b.extend(self.STRUCT.pack(*args))
        return b
    
    def read(self, rstream):
        return rstream.readStruct(self.STRUCT)

class NamedMessage(Message):
    NAME_LEN_STRUCT = struct.Struct('>H')

    def __init__(self, HEADER, STRUCT=None):
        Message.__init__(self, HEADER, STRUCT)
        
    def getBytes(self, name, *args):
        b = bytearray(self.HEADER)
        name = name.encode('utf-8')
        b.extend(self.NAME_LEN_STRUCT.pack(len(name)))
        b.extend(name)
        if self.STRUCT is not None:
            b.extend(self.STRUCT.pack(*args))
        return b

    def read(self, rstream):
        nameLen = rstream.readStruct(self.NAME_LEN_STRUCT)[0]
        try:
            name = rstream.read(nameLen).decode('utf-8')
        except UnicodeDecodeError as e:
            raise BadMessageError(e)
        return name, rstream.readStruct(self.STRUCT)


class NamedMessageEnd(Message):
    def __init__(self, HEADER, STRUCT=None):
        Message.__init__(self, HEADER, STRUCT)
        
    def getBytes(self, name, *args):
        b = bytearray(self.HEADER)
        if self.STRUCT is not None:
            b.extend(self.STRUCT.pack(*args))
        name = name.encode('utf-8')
        b.extend(leb128.encode_uleb128(len(name)))
        b.extend(name)
        return b

    def read(self, rstream):
        s = rstream.readStruct(self.STRUCT)
        nameLen = leb128.read_uleb128(rstream)
        try:
            name = rstream.read(nameLen).decode('utf-8')
        except UnicodeDecodeError as e:
            raise BadMessageError(e)
        return name, s


'''
kUnknown = -1,
kKeepAlive = 0x00,
kClientHello = 0x01,
kProtoUnsup = 0x02,
kServerHelloDone = 0x03,
kServerHello = 0x04,
kClientHelloDone = 0x05,
kEntryAssign = 0x10,
kEntryUpdate = 0x11,
kFlagsUpdate = 0x12,
kEntryDelete = 0x13,
kClearEntries = 0x14,
kExecuteRpc = 0x20,
kRpcResponse = 0x21
'''

# A keep alive message that the client sends
V2_KEEP_ALIVE = Message(b'\x00')
# A client hello message that a client sends
V2_CLIENT_HELLO = Message(b'\x01', '>H')
# A protocol version unsupported message that the server sends to a client
V2_PROTOCOL_UNSUPPORTED = Message(b'\x02', '>H')
# A server hello complete message that a server sends
V2_SERVER_HELLO_COMPLETE = Message(b'\x03')
# An entry assignment message
V2_ENTRY_ASSIGNMENT = NamedMessage(b'\x10', '>bHH')
# A field update message
V2_FIELD_UPDATE = Message(b'\x11', '>HH')

#
# TODO: How to deal with reading things?
#

# A keep alive message that the client sends
V3_KEEP_ALIVE = Message(b'\x00')
# A client hello message that a client sends
V3_CLIENT_HELLO = NamedMessageEnd(b'\x01', '>H')
# A protocol version unsupported message that the server sends to a client
V3_PROTOCOL_UNSUPPORTED = Message(b'\x02', '>H')
# A server hello complete message that a server sends
V3_SERVER_HELLO_COMPLETE = Message(b'\x03')
V3_SERVER_HELLO = NamedMessageEnd(b'\x04', 'b')
V3_CLIENT_HELLO_COMPLETE = Message(b'\x05')
# An entry assignment message
V3_ENTRY_ASSIGNMENT = NamedMessage(b'\x10', '>bHHb')
# A field update message
V3_FIELD_UPDATE = Message(b'\x11', '>HHb')
V3_FLAGS_UPDATE = Message(b'\x12', '>Hb')
V3_ENTRY_DELETE = Message(b'\x13', '>H')
V3_CLEAR_ENTRIES = Message(b'\x14', '>I')
V3_EXECUTE_RPC = NamedMessageEnd(b'\x20', '>HH')
V3_RPC_RESPONSE = NamedMessageEnd(b'\x21', '>HH')


#
# Build two dictionaries -- one for v2, one for v3
#


# Maybe what we do instead is define a single message class, which has 
# statics for v2 and v3... then we don't need these overloads


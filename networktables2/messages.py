
import struct

__all__ = ["BadMessageError", "PROTOCOL_REVISION",
           "KEEP_ALIVE", "CLIENT_HELLO", "PROTOCOL_UNSUPPORTED",
           "SERVER_HELLO_COMPLETE", "ENTRY_ASSIGNMENT", "FIELD_UPDATE"]

# The definitions of all of the protocol message types

class BadMessageError(IOError):
    pass


class MessageTypes(object):
    kKeepAlive = b'\x00'
    kClientHello = b'\x01'
    kProtoUnsup = b'\x02'
    kServerHelloDone = b'\x03'
    kServerHello = b'\x04'
    kClientHelloDone = b'\x05'
    kEntryAssign = b'\x10'
    kEntryUpdate = b'\x11'
    kFlagsUpdate = b'\x12'
    kEntryDelete = b'\x13'
    kClearEntries = b'\x14'
    kExecuteRpc = b'\x20'
    kRpcResponse = b'\x21'
    


PROTOCOL_REVISION = 0x0200

def getStringV2(rstream):
    pass

    # read 16 bits
    # read n bytes

def getStringV3(rstream):
    pass

    # read uleb
    # read n bytes

# Value storage is decoupled from value decoding/encoding
# .. which is different than now

# Message encoding/decoding must be directly coupled
# otherwise it's inefficient


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


bool_fmt = '?'
number_fmt = '>d'
# no string format
# no raw format


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



#
# TODO: How to deal with reading things?
#




#
# Build two dictionaries -- one for v2, one for v3
#


# Maybe what we do instead is define a single message class, which has 
# statics for v2 and v3... then we don't need these overloads


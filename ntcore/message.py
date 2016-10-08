'''
    Messages are stored separately from the wire format
    in order to support both protocol versions.
    
    This is a bit different from the C++ ntcore, as we have to decode
    the wire format a little bit differently anyways
'''


# .. but when the message is created, we don't know the protocol
#    to serialize to, so we have to keep it until we know

# Maybe we have a writeV2() and writeV3() function?

# Ok, just keep accumulating bytes, and join at the end

# Because of their differences, it's easier to define different 
# structs for each?

    #// Message data.  Use varies by message type.
    # MsgType type
    #std::string m_str;
    #std::shared_ptr<Value> m_value;
    #unsigned int m_id;  // also used for proto_rev
    #unsigned int m_flags;
    #unsigned int m_seq_num_uid;

# Need a base set that is guaranteed for each message type
from collections import namedtuple

from .constants import (
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



# The problem is that in this case then the generic pack stuff doesn't work
# as not everything has the right stuff
MessageType = namedtuple('MessageType', ['type', 'str', 'value',
                                         'id', 'flags', 'seq_num_uid'])

#EmptyMessage = namedtuple('EmptyMessage', ['type'])

# .. when I receive this, I need to know the rev
# .. when I create it, the rev needs to be set by someone else
#ClientHelloMessage = namedtuple('ClientHelloMessage', ['type', 'identity', 'proto_rev'])
#ServerHelloMessage = namedtuple('ServerHelloMessage', ['type', 'identity', 'proto_rev'])

#AssignMessage = namedtuple('AssignMessage', ['type', 'name', 'value', 'id', 'seq_num_uid', 'flags'])
#UpdateMessage = namedtuple('UpdateMessage', ['type', 'value', 'id', 'seq_num_uid'])

#FlagsMessage = namedtuple('FlagsMessage', ['type', 'id', 'flags'])
#DeleteMessage = namedtuple('DeleteMessage', ['type', 'id'])

#RpcResponseMessage = namedtuple('RpcResponseMessage', ['type', 'value', 'id', 'call_uid'])

class Message(object):
    
    # in ntcore, the encoder is the only one who knows about
    # the protocol version currently in use
    
    @staticmethod
    def clientHello(proto_rev, identity):
        return ClientHelloMessage(kClientHello, identity, proto_rev)
    
    @staticmethod
    def serverHello(flags, identity):
        return ServerHelloMessage(kServerHello, identity, flags)
    
    @staticmethod
    def serverHelloDone():
        return EmptyMessage(kServerHelloDone)
    
    @staticmethod
    def clientHelloDone():
        return EmptyMessage(kClientHelloDone)
    
    @staticmethod
    def entryAssign(name, msg_id, seq_num_uid, value, flags):
        return AssignMessage(kEntryAssign, name, msg_id, value, seq_num_uid, flags)
    
    @staticmethod
    def entryUpdate(entry_id, seq_num_uid, value):
        return UpdateMessage(kEntryUpdate, value, entry_id, seq_num_uid)
    
    @staticmethod
    def entryDelete(entry_id):
        return DeleteMessage(kEntryDelete, entry_id)

    @staticmethod
    def flagsUpdate(msg_id, flags):
        return FlagsMessage(kFlagsUpdate, msg_id, flags)
    
    @staticmethod
    def rpcResponse(rpc_id, call_uid, result):
        return RpcResponseMessage(kRpcResponse, result, rpc_id, call_uid)

    @staticmethod
    def read(rstream, codec, get_entry_type):
        msgtype = rstream.read(1)
        
        # switch type
        if msgtype == kKeepAlive:
            return EmptyMessage(msgtype)
        
        elif msgtype == kClientHello:
            proto_rev, = rstream.readStruct(codec.clientHello)
            
            identity = None
            if proto_rev >= 0x0300:
                identity = codec.read_string_v3(rstream)
                
            return ClientHelloMessage(msgtype, identity, proto_rev)
        
        elif msgtype == kProtoUnsup:
            proto_rev, = rstream.readStruct(codec.protoUnsup)
            return ProtoMessage(kProtoUnsup, proto_rev)
        
        elif msgtype == kServerHelloDone:
            return EmptyMessage(msgtype)
        
        elif msgtype == kServerHello:
            # nt3 only
            try:
                flags, str = rstream.readStruct(codec.serverHello)
            except AttributeError:
                raise # TODO: better error message
        
        elif msgtype == kEntryAssign:
            pass
        
        elif msgtype == kEntryUpdate:
            pass
            
            # getEntryFunc... how was I going to deal with that?
        
        elif msgtype == kFlagsUpdate:
            try:
                msg_id, flags = rstream.readStruct(codec.flagsUpdate)
            except AttributeError:
                raise # TODO: nt3 only
        
        elif msgtype == kEntryDelete:
            try:
                msg_id, = rstream.readStruct(codec.entryDelete)
            except AttributeError:
                raise # TODO: nt3 only
        
        elif msgtype == kClearEntries:
            try:
                magic, = rstream.readStruct(codec.clearEntries)
            except AttributeError:
                pass
        
        elif msgtype == kExecuteRpc:
            try:
                msg_id, seq_num_uid = rstream.readStruct(codec.executeRpc)
            except AttributeError:
                pass # todo: nt3 only

            msg_str = codec.read_string(rstream)
        
        elif msgtype == kRpcResponse:
            try:
                msg_id, seq_num_uid = rstream.readStruct(codec.executeRpc)
            except AttributeError:
                pass # todo: nt3 only

            msg_str = codec.read_string(rstream)
        
        raise ValueError("Unrecognized message type %s" % msgtype)
        
        # create message
    
    @staticmethod
    def write(msg, out, codec):
        msgtype = msg.type
        
        # switch type
        if msgtype == kKeepAlive:
            out.append(msgtype)
        
        elif msgtype == kClientHello:
            proto_rev = msg.id
            out.append(codec.clientHello.pack(proto_rev))
            
            if msg.id >= 0x0300:
                codec.write_string(msg.str, out)
                    
        elif msgtype == kProtoUnsup:
            proto_rev, = rstream.readStruct(codec.protoUnsup)
            return ProtoMessage(kProtoUnsup, proto_rev)
        
        elif msgtype == kServerHelloDone:
            return EmptyMessage(msgtype)
        
        elif msgtype == kServerHello:
            # nt3 only
            try:
                flags, str = rstream.readStruct(codec.serverHello)
            except AttributeError:
                raise # TODO: better error message
        
        elif msgtype == kEntryAssign:
            pass
        
        elif msgtype == kEntryUpdate:
            pass
            
            # getEntryFunc... how was I going to deal with that?
        
        elif msgtype == kFlagsUpdate:
            try:
                msg_id, flags = rstream.readStruct(codec.flagsUpdate)
            except AttributeError:
                raise # TODO: nt3 only
        
        elif msgtype == kEntryDelete:
            try:
                msg_id, = rstream.readStruct(codec.entryDelete)
            except AttributeError:
                raise # TODO: nt3 only
        
        elif msgtype == kClearEntries:
            try:
                magic, = rstream.readStruct(codec.clearEntries)
            except AttributeError:
                pass
        
        elif msgtype == kExecuteRpc:
            
            try:
                msg_id, seq_num_uid = rstream.readStruct(codec.executeRpc)
            except AttributeError:
                pass # todo: nt3 only

            msg_str = codec.read_string(rstream)
        
        elif msgtype == kRpcResponse:
        
        
        
        
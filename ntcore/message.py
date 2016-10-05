'''
    This is implemented a bit differently than how ntcore does it,
    because python is not C.

    When creating a new message, we assume that the caller really
    only cares about the bytes, so it just returns the bytes instead
    of a message object.
    
    When reading a message from the wire, then we deserialize into
    something.
'''


# .. but when the message is created, we don't know the protocol
#    to serialize to, so we have to keep it until we know

# Maybe we have a writeV2() and writeV3() function?

# Ok, just keep accumulating bytes, and join at the end

class Message(object):
    
    @staticmethod
    def clientHello(self_id):
        pass
    
    @staticmethod
    def clientHelloDone():
        pass
    
    @staticmethod
    def entryAssign(name, msg_id, seq_num, value, flags):
        pass
    
        # problem: what to do with value
    
    @staticmethod
    def entryDelete(entry_id):
        pass
    
    @staticmethod
    def entryUpdate(entry_id, seq_num, value):
        pass
    
        # problem: what to do with value?

    @staticmethod
    def flagsUpdate(self, msg_id, flags):
        pass
    
    @staticmethod
    def rpcResponse(rpc_id, call_uid, result):
        pass
    
    @staticmethod
    def serverHello(unknown, identity):
        pass
    
    @staticmethod
    def serverHelloDone():
        pass

def message_read():
    # read byte
    
    # if type is found, deserialize and return
    
    # if the type is not found, set error and return None
    
    pass
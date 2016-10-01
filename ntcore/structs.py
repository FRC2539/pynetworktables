
from collections import namedtuple

# data types
NT_UNASSIGNED = 0
NT_BOOLEAN = 0x01
NT_DOUBLE = 0x02
NT_STRING = 0x04
NT_RAW = 0x08
NT_BOOLEAN_ARRAY = 0x10
NT_DOUBLE_ARRAY = 0x20
NT_STRING_ARRAY = 0x40
NT_RPC = 0x80

# NetworkTables notifier kinds.
NT_NOTIFY_NONE = 0
NT_NOTIFY_IMMEDIATE = 0x01  # initial listener addition
NT_NOTIFY_LOCAL = 0x02      # changed locally
NT_NOTIFY_NEW = 0x04        # newly created entry
NT_NOTIFY_DELETE = 0x08     # deleted
NT_NOTIFY_UPDATE = 0x10     # value changed
NT_NOTIFY_FLAGS = 0x20      # flags changed 


#: NetworkTables Entry Information
EntryInfo = namedtuple('EntryInfo', [
    # Entry name
    'name',

    # Entry type
    'type',

    # Entry flags
    'flags',

    # Timestamp of last change to entry (type or value).
    'last_change',
])


#: NetworkTables Connection Information
ConnectionInfo = namedtuple('ConnectionInfo', [
    'remote_id',
    'remote_ip',
    'remote_port',
    'last_update',
    'protocol_version',
])


#: NetworkTables RPC Parameter Definition
RpcParamDef = namedtuple('RpcParamDef', [
    'name',
    'def_value',
])

#: NetworkTables RPC Result Definition
RpcResultDef = namedtuple('RpcResultDef', [
    'name',
    'type',
])

#: NetworkTables RPC Definition
RpcDefinition = namedtuple('RpcDefinition', [
    'version',
    'name',
    'params',
    'results',
])


#: NetworkTables RPC Call Data
RpcCallInfo = namedtuple('RpcCallInfo', [
    'rpc_id',
    'call_uid',
    'name',
    'params',
])
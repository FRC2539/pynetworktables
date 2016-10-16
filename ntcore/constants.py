


# data types
NT_UNASSIGNED =     b'\x00'
NT_BOOLEAN =        b'\x01'
NT_DOUBLE =         b'\x02'
NT_STRING =         b'\x04'
NT_RAW =            b'\x08'
NT_BOOLEAN_ARRAY =  b'\x10'
NT_DOUBLE_ARRAY =   b'\x20'
NT_STRING_ARRAY =   b'\x40'
NT_RPC =            b'\x80'

# NetworkTables notifier kinds.
NT_NOTIFY_NONE =        0x00
NT_NOTIFY_IMMEDIATE =   0x01 # initial listener addition
NT_NOTIFY_LOCAL =       0x02 # changed locally
NT_NOTIFY_NEW =         0x04 # newly created entry
NT_NOTIFY_DELETE =      0x08 # deleted
NT_NOTIFY_UPDATE =      0x10 # value changed
NT_NOTIFY_FLAGS =       0x20 # flags changed

# NetworkTables entry flags
NT_PERSISTENT = 0x01


# Message types
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

kClearAllMagic =    0xD06CB27A
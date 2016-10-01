'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

import base64
import threading

try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

from monotonic import monotonic

import logging
logger = logging.getLogger('nt')

from collections import namedtuple

class Entry(object):
    __slots__ = ['name', 'value', 'flags', 'id', 'seq_num', 'rpc_callback']
    
    def __init__(self, name, value=None, flags=0, seq_num=None):
        # We redundantly store the name so that it's available when accessing the
        # raw Entry* via the ID map.
        self.name = name
        
        # The current value and flags.
        self.value = value
        self.flags = flags
        
        # Unique ID for self entry as used in network messages.  The value is
        # assigned by the server, on the client this is 0xffff until an
        # entry assignment is received back from the server.
        self.id = 0xffff
        
        # Sequence number for update resolution.
        self.seq_num = seq_num
        
        # RPC callback function.  Null if either not an RPC or if the RPC is
        # polled.
        self.rpc_callback = None
        
        # Last UID used when calling self RPC (primarily for client use).  This
        # is incremented for each call.
        self.rpc_call_uid = 0
        
    def isPersistent(self):
        return (self.flags & NT_PERSISTENT) != 0 
    
    def increment_seqnum(self):
        self.seq_num += 1
        self.seq_num &= 0xffff

class Storage(object):
    
    def __init__(self, notifier, rpc_server):
        self.m_notifier = notifier
        self.m_rpc_server = rpc_server
        
        self.m_mutex = threading.Lock()
        self.m_entries = {}
        self.m_idmap = []
        self.m_rpc_results = {}
        self.m_rpc_blocking_calls = set()
        
        # If any persistent values have changed
        self.m_persistent_dirty = False
        
        # condition variable and termination flag for blocking on a RPC result
        self.m_terminating = False
        self.m_rpc_results_cond = threading.Condition()
        
        # configured by dispatcher at startup
        self.m_queue_outgoing = None
        self.m_server = True
    
    #def __del__(self):
    #    self.m_terminating = True
    #    with self.m_rpc_results_cond:
    #        self.m_rpc_results_cond.notify_all()
    
    def setOutgoing(self, queue_outgoing, server):
        with self.m_mutex:
            self.m_queue_outgoing = queue_outgoing
            self.m_server = server
    
    def clearOutgoing(self):
        self.m_queue_outgoing = nullptr
    
    def getEntryType(self, id):
        with self.m_mutex:
            if id >= self.m_idmap.size():
                return NT_UNASSIGNED
        
            entry = self.m_idmap[id]
            if not entry or not entry.value:
                return NT_UNASSIGNED
        
            return entry.value.type()
    
    
    void Storage.processIncoming(std.shared_ptr<Message> msg,
                                  NetworkConnection* conn,
                                  std.weak_ptr<NetworkConnection> conn_weak)
        std.unique_lock<std.mutex> lock(m_mutex)
        switch (msg.type())
        case Message.kKeepAlive:
            break;  # ignore
        case Message.kClientHello:
        case Message.kProtoUnsup:
        case Message.kServerHelloDone:
        case Message.kServerHello:
        case Message.kClientHelloDone:
            # shouldn't get these, ignore if we do
            break
        case Message.kEntryAssign:
            unsigned id = msg.id()
            name = msg.str()
            Entry* entry
            may_need_update = False
            if self.m_server:
                # if we're a server, id=0xffff requests are requests for an id
                # to be assigned, we need to send the assignment back to
                # the sender as well as all other connections.
                if id == 0xffff:
                    # see if it was already assigned; ignore if so.
                    if self.m_entries.count(name) != 0:
                        return
    
    
                    # create it locally
                    id = self.m_idmap.size()
                    new_entry = self.m_entries[name]
                    if not new_entry:
                        new_entry.reset(new Entry(name))
    
                    entry = new_entry.get()
                    entry.value = msg.value()
                    entry.flags = msg.flags()
                    entry.id = id
                    self.m_idmap.push_back(entry)
    
                    # update persistent dirty flag if it's persistent
                    if entry.isPersistent():
                        self.m_persistent_dirty = True
    
    
                    # notify
                    self.m_notifier.notifyEntry(name, entry.value, NT_NOTIFY_NEW)
    
                    # send the assignment to everyone (including the originator)
                    if self.m_queue_outgoing:
                        queue_outgoing = self.m_queue_outgoing
                        outmsg = Message.entryAssign(
                                          name, id, entry.seq_num, msg.value(), msg.flags())
                        lock.unlock()
                        queue_outgoing(outmsg, nullptr, nullptr)
    
                    return
    
                if id >= self.m_idmap.size() or not self.m_idmap[id]:
                    # ignore arbitrary entry assignments
                    # self can happen due to e.g. assignment to deleted entry
                    lock.unlock()
                    DEBUG("server: received assignment to unknown entry")
                    return
    
                entry = self.m_idmap[id]
    
            else:
                # clients simply accept assignments
                if id == 0xffff:
                    lock.unlock()
                    DEBUG("client: received entry assignment request?")
                    return
    
                if id >= len(self.m_idmap):
                    # resize idmap
                    self.m_idmap += [None]*(id - len(self.m_idmap)+1)
    
                entry = self.m_idmap[id]
                if not entry:
                    # create local
                    new_entry = self.m_entries[name]
                    if not new_entry:
                        # didn't exist at all (rather than just being a response to a
                        # id assignment request)
                        new_entry.reset(new Entry(name))
                        new_entry.value = msg.value()
                        new_entry.flags = msg.flags()
                        new_entry.id = id
                        self.m_idmap[id] = new_entry.get()
    
                        # notify
                        self.m_notifier.notifyEntry(name, new_entry.value, NT_NOTIFY_NEW)
                        return
    
                    may_need_update = True;  # we may need to send an update message
                    entry = new_entry.get()
                    entry.id = id
                    self.m_idmap[id] = entry
    
                    # if the received flags don't match what we sent, most likely
                    # updated flags locally in the interim; send flags update message.
                    if msg.flags() != entry.flags:
                        queue_outgoing = self.m_queue_outgoing
                        outmsg = Message.flagsUpdate(id, entry.flags)
                        lock.unlock()
                        queue_outgoing(outmsg, nullptr, nullptr)
                        lock.lock()
    
    
    
    
            # common client and server handling
    
            # already exists; ignore if sequence number not higher than local
            SequenceNumber seq_num(msg.seq_num_uid())
            if seq_num < entry.seq_num:
                if may_need_update:
                    queue_outgoing = self.m_queue_outgoing
                    outmsg = Message.entryUpdate(entry.id, entry.seq_num,
                                                       entry.value)
                    lock.unlock()
                    queue_outgoing(outmsg, nullptr, nullptr)
    
                return
    
    
            # sanity check: name should match id
            if msg.str() != entry.name:
                lock.unlock()
                DEBUG("entry assignment for same id with different name?")
                return
    
    
            unsigned notify_flags = NT_NOTIFY_UPDATE
    
            # don't update flags from a <3.0 remote (not part of message)
            # don't update flags if self is a server response to a client id request
            if not may_need_update and conn.proto_rev() >= 0x0300:
                # update persistent dirty flag if persistent flag changed
                if (entry.flags & NT_PERSISTENT) != (msg.flags() & NT_PERSISTENT):
                    self.m_persistent_dirty = True
    
                if entry.flags != msg.flags():
                    notify_flags |= NT_NOTIFY_FLAGS
    
                entry.flags = msg.flags()
    
    
            # update persistent dirty flag if the value changed and it's persistent
            if entry.isPersistent() and *entry.value != *msg.value():
                self.m_persistent_dirty = True
    
    
            # update local
            entry.value = msg.value()
            entry.seq_num = seq_num
    
            # notify
            self.m_notifier.notifyEntry(name, entry.value, notify_flags)
    
            # broadcast to all other connections (note for client there won't
            # be any other connections, don't bother)
            if self.m_server and self.m_queue_outgoing:
                queue_outgoing = self.m_queue_outgoing
                auto outmsg =
                    Message.entryAssign(entry.name, id, msg.seq_num_uid(),
                                         msg.value(), entry.flags)
                lock.unlock()
                queue_outgoing(outmsg, nullptr, conn)
    
            break
    
        case Message.kEntryUpdate:
            unsigned id = msg.id()
            if id >= self.m_idmap.size() or not self.m_idmap[id]:
                # ignore arbitrary entry updates
                # self can happen due to deleted entries
                lock.unlock()
                DEBUG("received update to unknown entry")
                return
    
            entry = self.m_idmap[id]
    
            # ignore if sequence number not higher than local
            SequenceNumber seq_num(msg.seq_num_uid())
            if seq_num <= entry.seq_num:
                return
    
    
            # update local
            entry.value = msg.value()
            entry.seq_num = seq_num
    
            # update persistent dirty flag if it's a persistent value
            if entry.isPersistent():
                self.m_persistent_dirty = True
    
    
            # notify
            self.m_notifier.notifyEntry(entry.name, entry.value, NT_NOTIFY_UPDATE)
    
            # broadcast to all other connections (note for client there won't
            # be any other connections, don't bother)
            if self.m_server and self.m_queue_outgoing:
                queue_outgoing = self.m_queue_outgoing
                lock.unlock()
                queue_outgoing(msg, nullptr, conn)
    
            break
    
        case Message.kFlagsUpdate:
            unsigned id = msg.id()
            if id >= self.m_idmap.size() or not self.m_idmap[id]:
                # ignore arbitrary entry updates
                # self can happen due to deleted entries
                lock.unlock()
                DEBUG("received flags update to unknown entry")
                return
    
            entry = self.m_idmap[id]
    
            # ignore if flags didn't actually change
            if entry.flags == msg.flags():
                return
    
    
            # update persistent dirty flag if persistent flag changed
            if (entry.flags & NT_PERSISTENT) != (msg.flags() & NT_PERSISTENT):
                self.m_persistent_dirty = True
    
    
            # update local
            entry.flags = msg.flags()
    
            # notify
            self.m_notifier.notifyEntry(entry.name, entry.value, NT_NOTIFY_FLAGS)
    
            # broadcast to all other connections (note for client there won't
            # be any other connections, don't bother)
            if self.m_server and self.m_queue_outgoing:
                queue_outgoing = self.m_queue_outgoing
                lock.unlock()
                queue_outgoing(msg, nullptr, conn)
    
            break
    
        case Message.kEntryDelete:
            unsigned id = msg.id()
            if id >= self.m_idmap.size() or not self.m_idmap[id]:
                # ignore arbitrary entry updates
                # self can happen due to deleted entries
                lock.unlock()
                DEBUG("received delete to unknown entry")
                return
    
            entry = self.m_idmap[id]
    
            # update persistent dirty flag if it's a persistent value
            if entry.isPersistent():
                self.m_persistent_dirty = True
    
    
            # delete it from idmap
            self.m_idmap[id] = nullptr
    
            # get entry (as we'll need it for notify) and erase it from the map
            # it should always be in the map, sanity check just in case
            i = self.m_entries.find(entry.name)
            if i != self.m_entries.end():
                entry2 = std.move(i.getValue());  # move the value out
                self.m_entries.erase(i)
    
                # notify
                self.m_notifier.notifyEntry(entry2.name, entry2.value, NT_NOTIFY_DELETE)
    
    
            # broadcast to all other connections (note for client there won't
            # be any other connections, don't bother)
            if self.m_server and self.m_queue_outgoing:
                queue_outgoing = self.m_queue_outgoing
                lock.unlock()
                queue_outgoing(msg, nullptr, conn)
    
            break
    
        case Message.kClearEntries:
            # update local
            _deleteAllEntriesImpl()
    
            # broadcast to all other connections (note for client there won't
            # be any other connections, don't bother)
            if self.m_server and self.m_queue_outgoing:
                queue_outgoing = self.m_queue_outgoing
                lock.unlock()
                queue_outgoing(msg, nullptr, conn)
    
            break
    
        case Message.kExecuteRpc:
            if not self.m_server:
                return;    # only process on server
    
            unsigned id = msg.id()
            if id >= self.m_idmap.size() or not self.m_idmap[id]:
                # ignore call to non-existent RPC
                # self can happen due to deleted entries
                lock.unlock()
                DEBUG("received RPC call to unknown entry")
                return
    
            entry = self.m_idmap[id]
            if not entry.value.IsRpc():
                lock.unlock()
                DEBUG("received RPC call to non-RPC entry")
                return
    
            self.m_rpc_server.processRpc(entry.name, msg, entry.rpc_callback,
                                    conn.uid(), [=](std.shared_ptr<Message> msg)
                c = conn_weak.lock()
                if c:
                    c.queueOutgoing(msg)
    
            })
            break
    
        case Message.kRpcResponse:
            if self.m_server:
                return;    # only process on client
    
            self.m_rpc_results.insert(std.make_pair(
                                     std.make_pair(msg.id(), msg.seq_num_uid()), msg.str()))
            self.m_rpc_results_cond.notify_all()
            break
    
        default:
            break
    
    def getInitialAssignments(self, conn, msgs):
        with self.m_mutex:
            conn.set_state(NetworkConnection.kSynchronized)
            for i in self.m_entries:
                entry = i.getValue().get()
                msgs.append(Message.entryAssign(i.getKey(), entry.id,
                                                entry.seq_num,
                                                entry.value, entry.flags))
    
    def applyInitialAssignments(self, conn, msgs, new_server, out_msgs):
        with self.m_mutex:
            if self.m_server:
                return    # should not do this on server
        
            conn.set_state(NetworkConnection.kSynchronized)
        
            update_msgs = []
        
            # clear existing id's
            for i in self.m_entries:
                i.getValue().id = 0xffff
        
            # clear existing idmap
            del self.m_idmap[:]
        
            # apply assignments
            for msg in msgs:
                if not msg.isType(Message.kEntryAssign):
                    logger.debug("client: received non-entry assignment request?")
                    continue
        
                msg_id = msg.id()
                if msg_id == 0xffff:
                    logger.debug("client: received entry assignment request?")
                    continue
        
                seq_num = msg.seq_num_uid()
                name = msg.str()
        
                entry = self.m_entries.get(name)
                if not entry:
                    # doesn't currently exist
                    entry = Entry(name, msg.value(), msg.flags(), seq_num)
                    self.m_entries[name] = entry
                    
                    # notify
                    self.m_notifier.notifyEntry(name, entry.value, NT_NOTIFY_NEW)
        
                else:
                    # if reconnect and sequence number not higher than local, we
                    # don't update the local value and instead send it back to the server
                    # as an update message
                    XXX # seq num bug
                    if not new_server and seq_num <= entry.seq_num:
                        update_msgs.append(Message.entryUpdate(entry.id, entry.seq_num, entry.value))
        
                    else:
                        entry.value = msg.value()
                        entry.seq_num = seq_num
                        notify_flags = NT_NOTIFY_UPDATE
                        # don't update flags from a <3.0 remote (not part of message)
                        if conn.proto_rev() >= 0x0300:
                            if entry.flags != msg.flags():
                                notify_flags |= NT_NOTIFY_FLAGS
        
                            entry.flags = msg.flags()
        
                        # notify
                        self.m_notifier.notifyEntry(name, entry.value, notify_flags)
        
                # set id and save to idmap
                entry.id = id
                if id >= len(self.m_idmap):
                    # resize idmap
                    self.m_idmap += [None]*(id - len(self.m_idmap)+1)
        
                self.m_idmap[id] = entry
        
        
            # generate assign messages for unassigned local entries
            for (auto& i : self.m_entries)
                entry = i.getValue().get()
                if entry.id != 0xffff:
                    continue
        
                out_msgs.emplace_back(Message.entryAssign(entry.name, entry.id,
                                       entry.seq_num,
                                       entry.value, entry.flags))
        
            queue_outgoing = self.m_queue_outgoing
            lock.unlock()
            for (auto& msg : update_msgs)
                queue_outgoing(msg, nullptr, nullptr)
    
    
    
    def getEntryValue(self, name):
        std.lock_guard<std.mutex> lock(m_mutex)
        i = self.m_entries.find(name)
        return i == self.m_entries.end() ? nullptr : i.getValue().value
    
    
    def setDefaultEntryValue(self, name, value):
        if not value:
            return False    # can't compare to a null value
    
        if name.empty():
            return False    # can't compare empty name
    
        with self.m_mutex:
            entry = self.m_entries.get(name)
            if entry:   # entry already exists
                old_value = entry.value
                
                # if types match return True
                if old_value and old_value.type() == value.type():
                    return True
                else:
                    return False    # entry exists but doesn't match type
        
            # if we've gotten here, does not exist, we can write it.
            # don't need to compare old value as we know it will assign
            entry = Entry(name, value)
            
            # if we're the server, an id if it doesn't have one
            if self.m_server and entry.id == 0xffff:
                entry.id = len(self.m_idmap)
                self.m_idmap.append(entry)
        
            # notify (for local listeners)
            if self.m_notifier.local_notifiers():
                # always a new entry if we got this far
                self.m_notifier.notifyEntry(name, value, NT_NOTIFY_NEW | NT_NOTIFY_LOCAL)
        
            # generate message
            if not self.m_queue_outgoing:
                return True
        
            queue_outgoing = self.m_queue_outgoing
            msg = Message.entryAssign(name, entry.id, entry.seq_num,
                                            entry.value, entry.flags)
            
        # Outside of mutex
        queue_outgoing(msg, None, None)
        return True
    
    def setEntryValue(self, name, value):
        if not name:
            return True
    
        if not value:
            return True
    
        with self.m_mutex:
            entry = self.m_entries.get(name)
            if not entry:
                entry = Entry(name)
            
            old_value = entry.value
            if old_value and old_value.type() != value.type():
                return False    # error on type mismatch
        
            entry.value = value
        
            # if we're the server, an id if it doesn't have one
            if self.m_server and entry.id == 0xffff:
                entry.id = len(self.m_idmap)
                self.m_idmap.append(entry)
            
            # update persistent dirty flag if value changed and it's persistent
            if entry.isPersistent() and old_value is not value:
                self.m_persistent_dirty = True
            
            # notify (for local listeners)
            if self.m_notifier.local_notifiers():
                if not old_value:
                    self.m_notifier.notifyEntry(name, value, NT_NOTIFY_NEW | NT_NOTIFY_LOCAL)
        
                elif old_value is not value:
                    self.m_notifier.notifyEntry(name, value, NT_NOTIFY_UPDATE | NT_NOTIFY_LOCAL)
            
            # generate message
            if not self.m_queue_outgoing:
                return True
        
            queue_outgoing = self.m_queue_outgoing
            msg = None
            
            if not old_value:
                msg = Message.entryAssign(name, entry.id, entry.seq_num,
                                                value, entry.flags)
        
            elif old_value is not value:
                entry.increment_seqnum()
                
                # don't send an update if we don't have an assigned id yet
                if entry.id != 0xffff:
                    msg = Message.entryUpdate(entry.id, entry.seq_num, value)
        
        # unlocked mutex
        if msg:
            queue_outgoing(msg, None, None)
            
        return True
    
    def setEntryTypeValue(self, name, value):
        if not name:
            return
    
        if not value:
            return
    
        with self.m_mutex:
            entry = self.m_entries.get(name)
            if not new_entry:
                entry = Entry(name)
        
            old_value = entry.value
            entry.value = value
            if old_value and old_value is value:
                return
            
            # if we're the server, an id if it doesn't have one
            if self.m_server and entry.id == 0xffff:
                entry.id = len(self.m_idmap)
                self.m_idmap.append(entry)
            
            # update persistent dirty flag if it's a persistent value
            if entry.isPersistent():
                self.m_persistent_dirty = True
            
            # notify (for local listeners)
            if self.m_notifier.local_notifiers():
                if not old_value:
                    self.m_notifier.notifyEntry(name, value, NT_NOTIFY_NEW | NT_NOTIFY_LOCAL)
        
                else:
                    self.m_notifier.notifyEntry(name, value, NT_NOTIFY_UPDATE | NT_NOTIFY_LOCAL)
            
            # generate message
            if not self.m_queue_outgoing:
                return
        
            queue_outgoing = self.m_queue_outgoing
            msg = None
            
            if not old_value or old_value.type() != value.type():
                entry.increment_seqnum()
                
                msg = Message.entryAssign(name, entry.id, entry.seq_num,
                                                value, entry.flags)
            else:
                entry.increment_seqnum()
                
                # don't send an update if we don't have an assigned id yet
                if entry.id != 0xffff:
                    msg = Message.entryUpdate(entry.id, entry.seq_num, value)
            
        # unlocked mutex
        if msg:
            queue_outgoing(msg, None, None)
    
    def setEntryFlags(self, name, int flags):
        if not name:
            return
    
        with self.m_mutex:
            entry = self.m_entries.get(name)
            if not entry:
                return
        
            if entry.flags == flags:
                return
            
            # update persistent dirty flag if persistent flag changed
            if (entry.flags & NT_PERSISTENT) != (flags & NT_PERSISTENT):
                self.m_persistent_dirty = True
            
            entry.flags = flags
        
            # notify
            self.m_notifier.notifyEntry(name, entry.value, NT_NOTIFY_FLAGS | NT_NOTIFY_LOCAL)
        
            # generate message
            if not self.m_queue_outgoing:
                return
        
            queue_outgoing = self.m_queue_outgoing
            entry_id = entry.id
            
        # don't send an update if we don't have an assigned id yet
        if entry_id != 0xffff:
            queue_outgoing(Message.flagsUpdate(entry_id, flags), None, None)
    
    def getEntryFlags(self, name):
        with self.m_mutex:
            entry = self.entries.get(name)
            return entry.flags if entry else 0
    
    def deleteEntry(self, name):
        with self.m_mutex:
            entry = self.m_entries.pop(name)
            if not entry:
                return
        
            entry_id = entry.id
        
            # update persistent dirty flag if it's a persistent value
            if entry.isPersistent():
                self.m_persistent_dirty = True
            
            if entry_id < len(self.m_idmap):
                self.m_idmap[entry_id] = None
            
            if not entry.value:
                return
            
            # notify
            self.m_notifier.notifyEntry(name, entry.value,
                                        NT_NOTIFY_DELETE | NT_NOTIFY_LOCAL)
        
            # if it had a value, message
            # don't send an update if we don't have an assigned id yet
            queue_outgoing = self.m_queue_outgoing
            
        if entry_id != 0xffff and queue_outgoing:
            queue_outgoing(Message.entryDelete(entry_id), None, None)
    
    def _deleteAllEntriesImpl(self):
        if not self.m_entries:
            return
    
        # only delete non-persistent values
        # can't erase without invalidating iterators, grab a list of keys
        for k in list(self.m_entries.keys()):
            entry = self.m_entries.get(k)
            if not entry.isPersistent():
                # notify it's being deleted
                if self.m_notifier.local_notifiers():
                    self.m_notifier.notifyEntry(i.getKey(), i.getValue().value,
                                           NT_NOTIFY_DELETE | NT_NOTIFY_LOCAL)
    
                # remove it from idmap
                if entry.id != 0xffff:
                    self.m_idmap[entry.id] = None
            else:
                # Delete it
                self.m_entries.pop(k)
    
    def deleteAllEntries(self):
        with self.m_mutex:
            if not self.m_entries:
                return
        
            self._deleteAllEntriesImpl()
        
            # generate message
            if not self.m_queue_outgoing:
                return
        
            queue_outgoing = self.m_queue_outgoing
        
        queue_outgoing(Message.clearEntries(), None, None)
    
    def getEntryInfo(self, prefix, types):
        with self.m_mutex:
            infos = []
            for k, entry in self.m_entries.items():
                if not k.startswith(prefix):
                    continue
                
                value = entry.value
                if not value:
                    continue
        
                if types != 0 and (types & value.type()) == 0:
                    continue
        
                info = EntryInfo(entry.name, value.type(), entry.flags, value.last_change())
                infos.append(info)
        
            return infos
    
    def notifyEntries(self, prefix, only):
        with self.m_mutex:
            for k, entry in self.m_entries.items():
                if not k.startswith(prefix):
                    continue
        
                self.m_notifier.notifyEntry(k, entry.value, NT_NOTIFY_IMMEDIATE,
                                            only)
    
    
    static void WriteString(std.ostream& os, str)
        ''' Escapes and writes a string, start and end double quotes '''
        os << '"'
        for (auto c : str)
            switch (c)
            case '\\':
                os << "\\\\"
                break
            case '\t':
                os << "\\t"
                break
            case '\n':
                os << "\\n"
                break
            case '"':
                os << "\\\""
                break
            default:
                if std.isprint(c):
                    os << c
                    break
    
    
                # Write out the escaped representation.
                os << "\\x"
                os << llvm.hexdigit((c >> 4) & 0xF)
                os << llvm.hexdigit((c >> 0) & 0xF)
    
    
        os << '"'
    
    
    bool Storage._getPersistentEntries(
        bool periodic,
        std.vector<std.pair<std.string, entries)
    const
        # copy values out of storage as quickly as possible so lock isn't held
            std.lock_guard<std.mutex> lock(m_mutex)
            # for periodic, don't re-save unless something has changed
            if periodic and not self.m_persistent_dirty:
                return False
    
            self.m_persistent_dirty = False
            entries.reserve(m_entries.size())
            for (auto& i : self.m_entries)
                entry = i.getValue().get()
                # only write persistent-flagged values
                if not entry.isPersistent():
                    continue
    
                entries.emplace_back(i.getKey(), entry.value)
    
    
    
        # sort in name order
        std.sort(entries.begin(), entries.end(),
                  []( std.pair<std.string, a,
                      std.pair<std.string, b)
            return a.first < b.first
        })
        return True
    
    
    static void SavePersistentImpl(
        std.ostream& os,
        llvm.ArrayRef<std.pair<std.string, entries)
        std.string base64_encoded
    
        # header
        os << "[NetworkTables Storage 3.0]\n"
    
        for (auto& i : entries)
            # type
            v = i.second
            if not v:
                continue
    
            switch (v.type())
            case NT_BOOLEAN:
                os << "boolean "
                break
            case NT_DOUBLE:
                os << "double "
                break
            case NT_STRING:
                os << "string "
                break
            case NT_RAW:
                os << "raw "
                break
            case NT_BOOLEAN_ARRAY:
                os << "array boolean "
                break
            case NT_DOUBLE_ARRAY:
                os << "array double "
                break
            case NT_STRING_ARRAY:
                os << "array string "
                break
            default:
                continue
    
    
            # name
            WriteString(os, i.first)
    
            # =
            os << '='
    
            # value
            switch (v.type())
            case NT_BOOLEAN:
                os << (v.GetBoolean() ? "True" : "False")
                break
            case NT_DOUBLE:
                os << v.GetDouble()
                break
            case NT_STRING:
                WriteString(os, v.GetString())
                break
            case NT_RAW:
                wpi.Base64Encode(v.GetRaw(), &base64_encoded)
                os << base64_encoded
                break
            case NT_BOOLEAN_ARRAY:
                first = True
                for (auto elem : v.GetBooleanArray())
                    if not first:
                        os << ','
    
                    first = False
                    os << (elem ? "True" : "False")
    
                break
    
            case NT_DOUBLE_ARRAY:
                first = True
                for (auto elem : v.GetDoubleArray())
                    if not first:
                        os << ','
    
                    first = False
                    os << elem
    
                break
    
            case NT_STRING_ARRAY:
                first = True
                for (auto& elem : v.GetStringArray())
                    if not first:
                        os << ','
    
                    first = False
                    WriteString(os, elem)
    
                break
    
            default:
                break
    
    
            # eol
            os << '\n'
    
    
    
    def savePersistent(self, os, periodic):
        std.vector<std.pair<std.string, entries
        if not _getPersistentEntries(periodic, &entries):
            return
    
        SavePersistentImpl(os, entries)
    
    
     char* Storage.savePersistent(StringRef filename, periodic)
        fn = filename
        tmp = filename
        tmp += ".tmp"
        bak = filename
        bak += ".bak"
    
        # Get entries before creating file
        std.vector<std.pair<std.string, entries
        if not _getPersistentEntries(periodic, &entries):
            return nullptr
    
        from configparser import RawConfigParser
    
         err = nullptr
    
        # start by writing to temporary file
        std.ofstream os(tmp)
        if not os:
            err = "could not open file"
            goto done
    
        DEBUG("saving persistent file '" << filename << "'")
        SavePersistentImpl(os, entries)
        os.flush()
        if not os:
            os.close()
            std.remove(tmp.c_str())
            err = "error saving file"
            goto done
    
        os.close()
    
        # Safely move to real file.  We ignore any failures related to the backup.
        std.remove(bak.c_str())
        std.rename(fn.c_str(), bak.c_str())
        if std.rename(tmp.c_str(), fn.c_str()) != 0:
            std.rename(bak.c_str(), fn.c_str());  # attempt to restore backup
            err = "could not rename temp file to real file"
            goto done
    
    
    done:
        # try again if there was an error
        if err and periodic:
            self.m_persistent_dirty = True
    
        return err
    
    
    ''' Extracts an escaped string token.  Does not unescape the string.
     * If a string cannot be matched, empty string is returned.
     * If the string is unterminated, empty tail string is returned.
     * The returned token includes the starting and trailing quotes (unless the
     * string is unterminated).
     * Returns a pair containing the extracted token (if any) and the remaining
     * tail string.
     '''
    static std.pair<llvm.StringRef, ReadStringToken(
        llvm.StringRef source)
        # Match opening quote
        if source.empty() or source.front() != '"':
            return std.make_pair(llvm.StringRef(), source)
    
    
        # Scan for ending double quote, for escaped as we go.
        size = source.size()
        std.size_t pos
        for (pos = 1; pos < size; ++pos)
            if source[pos] == '"' and source[pos - 1] != '\\':
                ++pos;  # we want to include the trailing quote in the result
                break
    
    
        return std.make_pair(source.slice(0, pos), source.substr(pos))
    
    
    static int fromxdigit(char ch)
        if ch >= 'a' and ch <= 'f':
            return (ch - 'a' + 10)
    
        elif ch >= 'A' and ch <= 'F':
            return (ch - 'A' + 10)
    
        else:
            return ch - '0'
    
    
    
    static void UnescapeString(llvm.StringRef source, dest)
        assert(source.size() >= 2 and source.front() == '"' and source.back() == '"')
        dest.clear()
        dest.reserve(source.size() - 2)
        for (s = source.begin() + 1, end = source.end() - 1; s != end; ++s)
            if *s != '\\':
                dest.push_back(*s)
                continue
    
            switch (*++s)
            case '\\':
            case '"':
                dest.push_back(s[-1])
                break
            case 't':
                dest.push_back('\t')
                break
            case 'n':
                dest.push_back('\n')
                break
            case 'x':
                if not isxdigit(*(s+1)):
                    dest.push_back('x');  # treat it like a unknown escape
                    break
    
                ch = fromxdigit(*++s)
                if isxdigit(*(s+1)):
                    ch <<= 4
                    ch |= fromxdigit(*++s)
    
                dest.push_back(static_cast<char>(ch))
                break
    
            default:
                dest.push_back(s[-1])
                break
    
    
    def loadPersistent(self, fname_or_fp):
        # accept
    
    bool Storage.loadPersistent(
        std.istream& is,
        std.function<void(std.size_t line, msg)> warn)
        std.string line_str
        line_num = 1
    
        # entries to add
        std.vector<std.pair<std.string, entries
    
        # declare these outside the loop to reduce reallocs
        std.string name, str
        std.vector<int> boolean_array
        std.vector<double> double_array
        std.vector<std.string> string_array
    
        # ignore blank lines and lines that start with ; or # (comments)
        while (std.getline(is, line_str))
            line = llvm.StringRef(line_str).trim()
            if not line.empty() and line.front() != ';' and line.front() != '#':
                break
    
    
    
        # header
        if line_str != "[NetworkTables Storage 3.0]":
            if warn:
                warn(line_num, "header line mismatch, rest of file")
    
            return False
    
    
        while (std.getline(is, line_str))
            line = llvm.StringRef(line_str).trim()
            ++line_num
    
            # ignore blank lines and lines that start with ; or # (comments)
            if line.empty() or line.front() == ';' or line.front() == '#':
                continue
    
    
            # type
            llvm.StringRef type_tok
            std.tie(type_tok, line) = line.split(' ')
            type = NT_UNASSIGNED
            if type_tok == "boolean":
                type = NT_BOOLEAN
    
            elif type_tok == "double":
                type = NT_DOUBLE
    
            elif type_tok == "string":
                type = NT_STRING
    
            elif type_tok == "raw":
                type = NT_RAW
    
            elif type_tok == "array":
                llvm.StringRef array_tok
                std.tie(array_tok, line) = line.split(' ')
                if array_tok == "boolean":
                    type = NT_BOOLEAN_ARRAY
    
                elif array_tok == "double":
                    type = NT_DOUBLE_ARRAY
    
                elif array_tok == "string":
                    type = NT_STRING_ARRAY
    
    
            if type == NT_UNASSIGNED:
                if warn:
                    warn(line_num, "unrecognized type")
    
                continue
    
    
            # name
            llvm.StringRef name_tok
            std.tie(name_tok, line) = ReadStringToken(line)
            if name_tok.empty():
                if warn:
                    warn(line_num, "missing name")
    
                continue
    
            if name_tok.back() != '"':
                if warn:
                    warn(line_num, "unterminated name string")
    
                continue
    
            UnescapeString(name_tok, &name)
    
            # =
            line = line.ltrim(" \t")
            if line.empty() or line.front() != '=':
                if warn:
                    warn(line_num, "expected = after name")
    
                continue
    
            line = line.drop_front().ltrim(" \t")
    
            # value
            std.shared_ptr<Value> value
            switch (type)
            case NT_BOOLEAN:
                # only True or False is accepted
                if line == "True":
                    value = Value.MakeBoolean(True)
    
                elif line == "False":
                    value = Value.MakeBoolean(False)
    
                else:
                    if warn:
                        warn(line_num, "unrecognized boolean value, not 'True' or 'False'")
    
                    goto next_line
    
                break
            case NT_DOUBLE:
                # need to convert to null-terminated string for strtod()
                str.clear()
                str += line
                char* end
                v = std.strtod(str.c_str(), &end)
                if *end != '\0':
                    if warn:
                        warn(line_num, "invalid double value")
    
                    goto next_line
    
                value = Value.MakeDouble(v)
                break
    
            case NT_STRING:
                llvm.StringRef str_tok
                std.tie(str_tok, line) = ReadStringToken(line)
                if str_tok.empty():
                    if warn:
                        warn(line_num, "missing string value")
    
                    goto next_line
    
                if str_tok.back() != '"':
                    if warn:
                        warn(line_num, "unterminated string value")
    
                    goto next_line
    
                UnescapeString(str_tok, &str)
                value = Value.MakeString(std.move(str))
                break
    
            case NT_RAW:
                wpi.Base64Decode(line, &str)
                value = Value.MakeRaw(std.move(str))
                break
            case NT_BOOLEAN_ARRAY:
                llvm.StringRef elem_tok
                boolean_array.clear()
                while (not line.empty())
                    std.tie(elem_tok, line) = line.split(',')
                    elem_tok = elem_tok.trim(" \t")
                    if elem_tok == "True":
                        boolean_array.push_back(1)
    
                    elif elem_tok == "False":
                        boolean_array.push_back(0)
    
                    else:
                        if warn:
                            warn(line_num,
                                 "unrecognized boolean value, not 'True' or 'False'")
                        goto next_line
    
    
    
                value = Value.makeBooleanArray(std.move(boolean_array))
                break
    
            case NT_DOUBLE_ARRAY:
                llvm.StringRef elem_tok
                double_array.clear()
                while (not line.empty())
                    std.tie(elem_tok, line) = line.split(',')
                    elem_tok = elem_tok.trim(" \t")
                    # need to convert to null-terminated string for strtod()
                    str.clear()
                    str += elem_tok
                    char* end
                    v = std.strtod(str.c_str(), &end)
                    if *end != '\0':
                        if warn:
                            warn(line_num, "invalid double value")
    
                        goto next_line
    
                    double_array.push_back(v)
    
    
                value = Value.MakeDoubleArray(std.move(double_array))
                break
    
            case NT_STRING_ARRAY:
                llvm.StringRef elem_tok
                string_array.clear()
                while (not line.empty())
                    std.tie(elem_tok, line) = ReadStringToken(line)
                    if elem_tok.empty():
                        if warn:
                            warn(line_num, "missing string value")
    
                        goto next_line
    
                    if elem_tok.back() != '"':
                        if warn:
                            warn(line_num, "unterminated string value")
    
                        goto next_line
    
    
                    UnescapeString(elem_tok, &str)
                    string_array.push_back(std.move(str))
    
                    line = line.ltrim(" \t")
                    if line.empty():
                        break
    
                    if line.front() != ',':
                        if warn:
                            warn(line_num, "expected comma between strings")
    
                        goto next_line
    
                    line = line.drop_front().ltrim(" \t")
    
    
                value = Value.MakeStringArray(std.move(string_array))
                break
    
            default:
                break
    
            if not name.empty() and value:
                entries.push_back(std.make_pair(std.move(name), std.move(value)))
    
    next_line:
            
    
    
        # copy values into storage as quickly as possible so lock isn't held
            std.vector<std.shared_ptr<Message>> msgs
            std.unique_lock<std.mutex> lock(m_mutex)
            for (auto& i : entries)
                new_entry = self.m_entries[i.first]
                if not new_entry:
                    new_entry.reset(new Entry(i.first))
    
                entry = new_entry.get()
                old_value = entry.value
                entry.value = i.second
                was_persist = entry.isPersistent()
                if not was_persist:
                    entry.flags |= NT_PERSISTENT
    
    
                # if we're the server, an id if it doesn't have one
                if self.m_server and entry.id == 0xffff:
                    unsigned id = self.m_idmap.size()
                    entry.id = id
                    self.m_idmap.push_back(entry)
    
    
                # notify (for local listeners)
                if self.m_notifier.local_notifiers():
                    if not old_value:
                        self.m_notifier.notifyEntry(i.first, i.second,
                                               NT_NOTIFY_NEW | NT_NOTIFY_LOCAL)
                    elif *old_value != *i.second:
                        unsigned notify_flags = NT_NOTIFY_UPDATE | NT_NOTIFY_LOCAL
                        if not was_persist:
                            notify_flags |= NT_NOTIFY_FLAGS
    
                        self.m_notifier.notifyEntry(i.first, i.second, notify_flags)
    
    
    
                if not self.m_queue_outgoing:
                    continue;    # shortcut
    
                ++entry.seq_num
    
                # put on update queue
                if not old_value or old_value.type() != i.second.type():
                    msgs.emplace_back(Message.entryAssign(i.first, entry.id,
                                                           entry.seq_num,
                                                           i.second, entry.flags))
                elif entry.id != 0xffff:
                    # don't send an update if we don't have an assigned id yet
                    if *old_value != *i.second:
                        msgs.emplace_back(Message.entryUpdate(
                                              entry.id, entry.seq_num, i.second))
                    if not was_persist:
                        msgs.emplace_back(Message.flagsUpdate(entry.id, entry.flags))
    
    
    
    
            if self.m_queue_outgoing:
                queue_outgoing = self.m_queue_outgoing
                lock.unlock()
                for (auto& msg : msgs)
                    queue_outgoing(std.move(msg), nullptr, nullptr)
    
    
    
    
        return True
    
    def createRpc(self, name, defn, callback):
        if not name or defn or not callback:
            return
    
        with self.m_mutex:
            if not self.m_server:
                return    # only server can create RPCs
            
            entry = self.m_entries.get(name)
            if not entry:
                entry = Entry(name)
            
            old_value = entry.value
            value = Value.MakeRpc(defn)
            entry.value = value
        
            # set up the callback
            entry.rpc_callback = callback
        
            # start the RPC server
            self.m_rpc_server.start()
        
            if old_value and old_value is value:
                return
            
            # assign an id if it doesn't have one
            if entry.id == 0xffff:
                entry.id = len(self.m_idmap)
                self.m_idmap.append(entry)
            
            # generate message
            if not self.m_queue_outgoing:
                return
        
            queue_outgoing = self.m_queue_outgoing
            msg = None
            
            if not old_value or old_value.type() != value.type():
                entry.increment_seqnum()
                msg = Message.entryAssign(name, entry.id, entry.seq_num,
                                                value, entry.flags)
            else:
                entry.increment_seqnum()
                msg = Message.entryUpdate(entry.id, entry.seq_num, value)
                
        # unlocked mutex
        if msg:
            queue_outgoing(msg, None, None)
    
    def createPolledRpc(self, name, defn):
        if not name or not defn:
            return
        
        with self.m_mutex:
            if not self.m_server:
                return    # only server can create RPCs
            
            entry = self.m_entries.get(name)
            if not entry:
                entry = Entry(name)
        
            entry = new_entry.get()
            old_value = entry.value
            value = Value.MakeRpc(defn)
            entry.value = value
        
            # a None callback indicates a polled RPC
            entry.rpc_callback = None
        
            if old_value and old_value is value:
                return
            
            # assign an id if it doesn't have one
            if entry.id == 0xffff:
                entry.id = len(self.m_idmap)
                self.m_idmap.append(entry)
            
            # generate message
            if not self.m_queue_outgoing:
                return
        
            queue_outgoing = self.m_queue_outgoing
            msg = None
            
            if not old_value or old_value.type() != value.type():
                entry.increment_seqnum()
                msg = Message.entryAssign(name, entry.id, entry.seq_num,
                                                value, entry.flags)
            else:
                entry.increment_seqnum()
                msg = Message.entryUpdate(entry.id, entry.seq_num, value)
                
        # unlocked mutex
        if msg:
            queue_outgoing(msg, None, None)
    
    def callRpc(self, name, params):
        self.m_mutex.acquire()
        locked = True
        try:
            entry = self.m_entries.get(name)
            if not entry:
                return 0
            
            if not entry.value.isRpc():
                return 0
        
            entry.rpc_call_uid += 1
            entry.rpc_call_uid &= 0xffff
            
            combined_uid = (entry.id << 16) | entry.rpc_call_uid
            msg = Message.executeRpc(entry.id, entry.rpc_call_uid, params)
            if self.m_server:
                # RPCs are unlikely to be used locally on the server, handle it
                # gracefully anyway.
                rpc_callback = entry.rpc_callback
                
                self.m_mutex.release()
                locked = False
                
                self.m_rpc_server.processRpc(name, msg, rpc_callback, 0xffff,
                                             self._process_rpc)
            else:
                queue_outgoing = self.m_queue_outgoing
                
                self.m_mutex.release()
                locked = False
                
                queue_outgoing(msg, None, None)
        
            return combined_uid
        finally:
            if locked:
                self.m_mutex.release()
    
    def _process_rpc(msg):
        with self.m_mutex:
            self.m_rpc_results[(msg.id(), msg.seq_num_uid())] = msg.str()
            self.m_rpc_results_cond.notify_all()
    
    def getRpcResult(self, blocking, call_uid, time_out=-1):
        with self.m_mutex:
            # only allow one blocking call per rpc call uid
            if call_uid in self.m_rpc_blocking_calls:
                return False, None
        
            self.m_rpc_blocking_calls.add(call_uid)
            wait_until = monotonic() + time_out
        
            try:
                while True:
                    result = self.m_rpc_results.get(call_uid) 
                    if not result:
                        if not blocking or self.m_terminating:
                            return False, None
            
                        if time_out <= 0:
                            self.m_rpc_results_cond.wait()
                        else:
                            ttw = monotonic() - wait_until
                            if ttw <= 0:
                                return False, None
                            
                            self.m_rpc_results_cond.wait(ttw)
            
                        # if element does not exist, have been canceled
                        if call_uid not in self.m_rpc_blocking_calls:
                            return False, None
            
                        if self.m_terminating:
                            return False, None
            
                        continue
                    
                    self.m_rpc_results.pop(call_uid, None)
                    return True, result
            finally:
                try:
                    self.m_rpc_blocking_calls.remove(call_uid)
                except KeyError:
                    pass
    
    def cancelBlockingRpcResult(self, int call_uid):
        with self.m_mutex:
            # safe to erase even if id does not exist
            self.m_rpc_blocking_calls.erase(call_uid)
            self.m_rpc_results_cond.notify_all()
    

'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "Storage.h"

#include <cctype>
#include <string>
#include <tuple>

#include "llvm/StringExtras.h"
#include "support/Base64.h"
#include "Log.h"
#include "NetworkConnection.h"

using namespace nt

ATOMIC_STATIC_INIT(Storage)

Storage.Storage()
    : Storage(Notifier.GetInstance(), RpcServer.GetInstance()) {

Storage.Storage(Notifier& notifier, rpc_server)
    : m_notifier(notifier), m_rpc_server(rpc_server)
    m_terminating = False


Storage.~Storage()
    Logger.GetInstance().SetLogger(nullptr)
    m_terminating = True
    m_rpc_results_cond.notify_all()


def setOutgoing(self, queue_outgoing, server):
    std.lock_guard<std.mutex> lock(m_mutex)
    m_queue_outgoing = queue_outgoing
    m_server = server


def clearOutgoing(self):
    m_queue_outgoing = nullptr


def getEntryType(self, int id):
    std.lock_guard<std.mutex> lock(m_mutex)
    if id >= m_idmap.size():
        return NT_UNASSIGNED

    entry = m_idmap[id]
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
        if m_server:
            # if we're a server, id=0xffff requests are requests for an id
            # to be assigned, we need to send the assignment back to
            # the sender as well as all other connections.
            if id == 0xffff:
                # see if it was already assigned; ignore if so.
                if m_entries.count(name) != 0:
                    return


                # create it locally
                id = m_idmap.size()
                new_entry = m_entries[name]
                if not new_entry:
                    new_entry.reset(new Entry(name))

                entry = new_entry.get()
                entry.value = msg.value()
                entry.flags = msg.flags()
                entry.id = id
                m_idmap.push_back(entry)

                # update persistent dirty flag if it's persistent
                if entry.isPersistent():
                    m_persistent_dirty = True


                # notify
                m_notifier.notifyEntry(name, entry.value, NT_NOTIFY_NEW)

                # send the assignment to everyone (including the originator)
                if m_queue_outgoing:
                    queue_outgoing = m_queue_outgoing
                    outmsg = Message.entryAssign(
                                      name, id, entry.seq_num.value(), msg.value(), msg.flags())
                    lock.unlock()
                    queue_outgoing(outmsg, nullptr, nullptr)

                return

            if id >= m_idmap.size() or not m_idmap[id]:
                # ignore arbitrary entry assignments
                # self can happen due to e.g. assignment to deleted entry
                lock.unlock()
                DEBUG("server: received assignment to unknown entry")
                return

            entry = m_idmap[id]

        else:
            # clients simply accept assignments
            if id == 0xffff:
                lock.unlock()
                DEBUG("client: received entry assignment request?")
                return

            if id >= m_idmap.size():
                m_idmap.resize(id+1)

            entry = m_idmap[id]
            if not entry:
                # create local
                new_entry = m_entries[name]
                if not new_entry:
                    # didn't exist at all (rather than just being a response to a
                    # id assignment request)
                    new_entry.reset(new Entry(name))
                    new_entry.value = msg.value()
                    new_entry.flags = msg.flags()
                    new_entry.id = id
                    m_idmap[id] = new_entry.get()

                    # notify
                    m_notifier.notifyEntry(name, new_entry.value, NT_NOTIFY_NEW)
                    return

                may_need_update = True;  # we may need to send an update message
                entry = new_entry.get()
                entry.id = id
                m_idmap[id] = entry

                # if the received flags don't match what we sent, most likely
                # updated flags locally in the interim; send flags update message.
                if msg.flags() != entry.flags:
                    queue_outgoing = m_queue_outgoing
                    outmsg = Message.flagsUpdate(id, entry.flags)
                    lock.unlock()
                    queue_outgoing(outmsg, nullptr, nullptr)
                    lock.lock()




        # common client and server handling

        # already exists; ignore if sequence number not higher than local
        SequenceNumber seq_num(msg.seq_num_uid())
        if seq_num < entry.seq_num:
            if may_need_update:
                queue_outgoing = m_queue_outgoing
                outmsg = Message.entryUpdate(entry.id, entry.seq_num.value(),
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
                m_persistent_dirty = True

            if entry.flags != msg.flags():
                notify_flags |= NT_NOTIFY_FLAGS

            entry.flags = msg.flags()


        # update persistent dirty flag if the value changed and it's persistent
        if entry.isPersistent() and *entry.value != *msg.value():
            m_persistent_dirty = True


        # update local
        entry.value = msg.value()
        entry.seq_num = seq_num

        # notify
        m_notifier.notifyEntry(name, entry.value, notify_flags)

        # broadcast to all other connections (note for client there won't
        # be any other connections, don't bother)
        if m_server and m_queue_outgoing:
            queue_outgoing = m_queue_outgoing
            auto outmsg =
                Message.entryAssign(entry.name, id, msg.seq_num_uid(),
                                     msg.value(), entry.flags)
            lock.unlock()
            queue_outgoing(outmsg, nullptr, conn)

        break

    case Message.kEntryUpdate:
        unsigned id = msg.id()
        if id >= m_idmap.size() or not m_idmap[id]:
            # ignore arbitrary entry updates
            # self can happen due to deleted entries
            lock.unlock()
            DEBUG("received update to unknown entry")
            return

        entry = m_idmap[id]

        # ignore if sequence number not higher than local
        SequenceNumber seq_num(msg.seq_num_uid())
        if seq_num <= entry.seq_num:
            return


        # update local
        entry.value = msg.value()
        entry.seq_num = seq_num

        # update persistent dirty flag if it's a persistent value
        if entry.isPersistent():
            m_persistent_dirty = True


        # notify
        m_notifier.notifyEntry(entry.name, entry.value, NT_NOTIFY_UPDATE)

        # broadcast to all other connections (note for client there won't
        # be any other connections, don't bother)
        if m_server and m_queue_outgoing:
            queue_outgoing = m_queue_outgoing
            lock.unlock()
            queue_outgoing(msg, nullptr, conn)

        break

    case Message.kFlagsUpdate:
        unsigned id = msg.id()
        if id >= m_idmap.size() or not m_idmap[id]:
            # ignore arbitrary entry updates
            # self can happen due to deleted entries
            lock.unlock()
            DEBUG("received flags update to unknown entry")
            return

        entry = m_idmap[id]

        # ignore if flags didn't actually change
        if entry.flags == msg.flags():
            return


        # update persistent dirty flag if persistent flag changed
        if (entry.flags & NT_PERSISTENT) != (msg.flags() & NT_PERSISTENT):
            m_persistent_dirty = True


        # update local
        entry.flags = msg.flags()

        # notify
        m_notifier.notifyEntry(entry.name, entry.value, NT_NOTIFY_FLAGS)

        # broadcast to all other connections (note for client there won't
        # be any other connections, don't bother)
        if m_server and m_queue_outgoing:
            queue_outgoing = m_queue_outgoing
            lock.unlock()
            queue_outgoing(msg, nullptr, conn)

        break

    case Message.kEntryDelete:
        unsigned id = msg.id()
        if id >= m_idmap.size() or not m_idmap[id]:
            # ignore arbitrary entry updates
            # self can happen due to deleted entries
            lock.unlock()
            DEBUG("received delete to unknown entry")
            return

        entry = m_idmap[id]

        # update persistent dirty flag if it's a persistent value
        if entry.isPersistent():
            m_persistent_dirty = True


        # delete it from idmap
        m_idmap[id] = nullptr

        # get entry (as we'll need it for notify) and erase it from the map
        # it should always be in the map, sanity check just in case
        i = m_entries.find(entry.name)
        if i != m_entries.end():
            entry2 = std.move(i.getValue());  # move the value out
            m_entries.erase(i)

            # notify
            m_notifier.notifyEntry(entry2.name, entry2.value, NT_NOTIFY_DELETE)


        # broadcast to all other connections (note for client there won't
        # be any other connections, don't bother)
        if m_server and m_queue_outgoing:
            queue_outgoing = m_queue_outgoing
            lock.unlock()
            queue_outgoing(msg, nullptr, conn)

        break

    case Message.kClearEntries:
        # update local
        _deleteAllEntriesImpl()

        # broadcast to all other connections (note for client there won't
        # be any other connections, don't bother)
        if m_server and m_queue_outgoing:
            queue_outgoing = m_queue_outgoing
            lock.unlock()
            queue_outgoing(msg, nullptr, conn)

        break

    case Message.kExecuteRpc:
        if not m_server:
            return;    # only process on server

        unsigned id = msg.id()
        if id >= m_idmap.size() or not m_idmap[id]:
            # ignore call to non-existent RPC
            # self can happen due to deleted entries
            lock.unlock()
            DEBUG("received RPC call to unknown entry")
            return

        entry = m_idmap[id]
        if not entry.value.IsRpc():
            lock.unlock()
            DEBUG("received RPC call to non-RPC entry")
            return

        m_rpc_server.processRpc(entry.name, msg, entry.rpc_callback,
                                conn.uid(), [=](std.shared_ptr<Message> msg)
            c = conn_weak.lock()
            if c:
                c.queueOutgoing(msg)

        })
        break

    case Message.kRpcResponse:
        if m_server:
            return;    # only process on client

        m_rpc_results.insert(std.make_pair(
                                 std.make_pair(msg.id(), msg.seq_num_uid()), msg.str()))
        m_rpc_results_cond.notify_all()
        break

    default:
        break



void Storage.getInitialAssignments(
    NetworkConnection& conn, msgs)
    std.lock_guard<std.mutex> lock(m_mutex)
    conn.set_state(NetworkConnection.kSynchronized)
    for (auto& i : m_entries)
        entry = i.getValue().get()
        msgs.emplace_back(Message.entryAssign(i.getKey(), entry.id,
                                                entry.seq_num.value(),
                                                entry.value, entry.flags))



void Storage.applyInitialAssignments(
    NetworkConnection& conn, msgs,
    bool new_server, out_msgs)
    std.unique_lock<std.mutex> lock(m_mutex)
    if m_server:
        return;    # should not do self on server


    conn.set_state(NetworkConnection.kSynchronized)

    std.vector<std.shared_ptr<Message>> update_msgs

    # clear existing id's
    for (auto& i : m_entries)
        i.getValue().id = 0xffff


    # clear existing idmap
    m_idmap.resize(0)

    # apply assignments
    for (auto& msg : msgs)
        if not msg.isType(Message.kEntryAssign):
            DEBUG("client: received non-entry assignment request?")
            continue


        unsigned id = msg.id()
        if id == 0xffff:
            DEBUG("client: received entry assignment request?")
            continue


        SequenceNumber seq_num(msg.seq_num_uid())
        name = msg.str()

        entry = m_entries[name]
        if not entry:
            # doesn't currently exist
            entry.reset(new Entry(name))
            entry.value = msg.value()
            entry.flags = msg.flags()
            entry.seq_num = seq_num
            # notify
            m_notifier.notifyEntry(name, entry.value, NT_NOTIFY_NEW)

        else:
            # if reconnect and sequence number not higher than local, we
            # don't update the local value and instead send it back to the server
            # as an update message
            if not new_server and seq_num <= entry.seq_num:
                update_msgs.emplace_back(Message.entryUpdate(
                                             entry.id, entry.seq_num.value(), entry.value))

            else:
                entry.value = msg.value()
                entry.seq_num = seq_num
                unsigned notify_flags = NT_NOTIFY_UPDATE
                # don't update flags from a <3.0 remote (not part of message)
                if conn.proto_rev() >= 0x0300:
                    if entry.flags != msg.flags():
                        notify_flags |= NT_NOTIFY_FLAGS

                    entry.flags = msg.flags()

                # notify
                m_notifier.notifyEntry(name, entry.value, notify_flags)



        # set id and save to idmap
        entry.id = id
        if id >= m_idmap.size():
            m_idmap.resize(id+1)

        m_idmap[id] = entry.get()


    # generate assign messages for unassigned local entries
    for (auto& i : m_entries)
        entry = i.getValue().get()
        if entry.id != 0xffff:
            continue

        out_msgs.emplace_back(Message.entryAssign(entry.name, entry.id,
                               entry.seq_num.value(),
                               entry.value, entry.flags))

    queue_outgoing = m_queue_outgoing
    lock.unlock()
    for (auto& msg : update_msgs)
        queue_outgoing(msg, nullptr, nullptr)



def getEntryValue(self, name):
    std.lock_guard<std.mutex> lock(m_mutex)
    i = m_entries.find(name)
    return i == m_entries.end() ? nullptr : i.getValue().value


bool Storage.setDefaultEntryValue(StringRef name,
                                   std.shared_ptr<Value> value)
    if not value:
        return False;    # can't compare to a null value

    if name.empty():
        return False;    # can't compare empty name

    std.unique_lock<std.mutex> lock(m_mutex)
    new_entry = m_entries[name]
    if (new_entry)   # entry already exists
        old_value = new_entry.value
        # if types match return True
        if old_value and old_value.type() == value.type():
            return True

        else:
            return False;    # entry exists but doesn't match type



    # if we've gotten here, does not exist, we can write it.
    new_entry.reset(new Entry(name))
    entry = new_entry.get()
    # don't need to compare old value as we know it will assign
    entry.value = value

    # if we're the server, an id if it doesn't have one
    if m_server and entry.id == 0xffff:
        unsigned id = m_idmap.size()
        entry.id = id
        m_idmap.push_back(entry)


    # notify (for local listeners)
    if m_notifier.local_notifiers():
        # always a entry if we got self far
        m_notifier.notifyEntry(name, value, NT_NOTIFY_NEW | NT_NOTIFY_LOCAL)


    # generate message
    if not m_queue_outgoing:
        return True

    queue_outgoing = m_queue_outgoing
    msg = Message.entryAssign(name, entry.id, entry.seq_num.value(),
                                    value, entry.flags)
    lock.unlock()
    queue_outgoing(msg, nullptr, nullptr)
    return True


def setEntryValue(self, name, value):
    if name.empty():
        return True

    if not value:
        return True

    std.unique_lock<std.mutex> lock(m_mutex)
    new_entry = m_entries[name]
    if not new_entry:
        new_entry.reset(new Entry(name))

    entry = new_entry.get()
    old_value = entry.value
    if old_value and old_value.type() != value.type():
        return False;    # error on type mismatch

    entry.value = value

    # if we're the server, an id if it doesn't have one
    if m_server and entry.id == 0xffff:
        unsigned id = m_idmap.size()
        entry.id = id
        m_idmap.push_back(entry)


    # update persistent dirty flag if value changed and it's persistent
    if entry.isPersistent() and *old_value != *value:
        m_persistent_dirty = True


    # notify (for local listeners)
    if m_notifier.local_notifiers():
        if not old_value:
            m_notifier.notifyEntry(name, value, NT_NOTIFY_NEW | NT_NOTIFY_LOCAL)

        elif *old_value != *value:
            m_notifier.notifyEntry(name, value, NT_NOTIFY_UPDATE | NT_NOTIFY_LOCAL)



    # generate message
    if not m_queue_outgoing:
        return True

    queue_outgoing = m_queue_outgoing
    if not old_value:
        msg = Message.entryAssign(name, entry.id, entry.seq_num.value(),
                                        value, entry.flags)
        lock.unlock()
        queue_outgoing(msg, nullptr, nullptr)

    elif *old_value != *value:
        ++entry.seq_num
        # don't send an update if we don't have an assigned id yet
        if entry.id != 0xffff:
            auto msg =
                Message.entryUpdate(entry.id, entry.seq_num.value(), value)
            lock.unlock()
            queue_outgoing(msg, nullptr, nullptr)


    return True


def setEntryTypeValue(self, name, value):
    if name.empty():
        return

    if not value:
        return

    std.unique_lock<std.mutex> lock(m_mutex)
    new_entry = m_entries[name]
    if not new_entry:
        new_entry.reset(new Entry(name))

    entry = new_entry.get()
    old_value = entry.value
    entry.value = value
    if old_value and *old_value == *value:
        return


    # if we're the server, an id if it doesn't have one
    if m_server and entry.id == 0xffff:
        unsigned id = m_idmap.size()
        entry.id = id
        m_idmap.push_back(entry)


    # update persistent dirty flag if it's a persistent value
    if entry.isPersistent():
        m_persistent_dirty = True


    # notify (for local listeners)
    if m_notifier.local_notifiers():
        if not old_value:
            m_notifier.notifyEntry(name, value, NT_NOTIFY_NEW | NT_NOTIFY_LOCAL)

        else:
            m_notifier.notifyEntry(name, value, NT_NOTIFY_UPDATE | NT_NOTIFY_LOCAL)



    # generate message
    if not m_queue_outgoing:
        return

    queue_outgoing = m_queue_outgoing
    if not old_value or old_value.type() != value.type():
        ++entry.seq_num
        msg = Message.entryAssign(name, entry.id, entry.seq_num.value(),
                                        value, entry.flags)
        lock.unlock()
        queue_outgoing(msg, nullptr, nullptr)

    else:
        ++entry.seq_num
        # don't send an update if we don't have an assigned id yet
        if entry.id != 0xffff:
            auto msg =
                Message.entryUpdate(entry.id, entry.seq_num.value(), value)
            lock.unlock()
            queue_outgoing(msg, nullptr, nullptr)




def setEntryFlags(self, name, int flags):
    if name.empty():
        return

    std.unique_lock<std.mutex> lock(m_mutex)
    i = m_entries.find(name)
    if i == m_entries.end():
        return

    entry = i.getValue().get()
    if entry.flags == flags:
        return


    # update persistent dirty flag if persistent flag changed
    if (entry.flags & NT_PERSISTENT) != (flags & NT_PERSISTENT):
        m_persistent_dirty = True


    entry.flags = flags

    # notify
    m_notifier.notifyEntry(name, entry.value, NT_NOTIFY_FLAGS | NT_NOTIFY_LOCAL)

    # generate message
    if not m_queue_outgoing:
        return

    queue_outgoing = m_queue_outgoing
    unsigned id = entry.id
    # don't send an update if we don't have an assigned id yet
    if id != 0xffff:
        lock.unlock()
        queue_outgoing(Message.flagsUpdate(id, flags), nullptr, nullptr)



unsigned int Storage.getEntryFlags(StringRef name)
    std.lock_guard<std.mutex> lock(m_mutex)
    i = m_entries.find(name)
    return i == m_entries.end() ? 0 : i.getValue().flags


def deleteEntry(self, name):
    std.unique_lock<std.mutex> lock(m_mutex)
    i = m_entries.find(name)
    if i == m_entries.end():
        return

    entry = std.move(i.getValue())
    unsigned id = entry.id

    # update persistent dirty flag if it's a persistent value
    if entry.isPersistent():
        m_persistent_dirty = True


    m_entries.erase(i);  # erase from map
    if id < m_idmap.size():
        m_idmap[id] = nullptr


    if not entry.value:
        return


    # notify
    m_notifier.notifyEntry(name, entry.value,
                           NT_NOTIFY_DELETE | NT_NOTIFY_LOCAL)

    # if it had a value, message
    # don't send an update if we don't have an assigned id yet
    if id != 0xffff:
        if not m_queue_outgoing:
            return

        queue_outgoing = m_queue_outgoing
        lock.unlock()
        queue_outgoing(Message.entryDelete(id), nullptr, nullptr)



def _deleteAllEntriesImpl(self):
    if m_entries.empty():
        return


    # only delete non-persistent values
    # can't erase without invalidating iterators, build a map
    EntriesMap entries
    for (auto& i : m_entries)
        entry = i.getValue().get()
        if not entry.isPersistent():
            # notify it's being deleted
            if m_notifier.local_notifiers():
                m_notifier.notifyEntry(i.getKey(), i.getValue().value,
                                       NT_NOTIFY_DELETE | NT_NOTIFY_LOCAL)

            # remove it from idmap
            if entry.id != 0xffff:
                m_idmap[entry.id] = nullptr


        else:
            # add it to entries
            entries.insert(std.make_pair(i.getKey(), std.move(i.getValue())))


    m_entries.swap(entries)


def deleteAllEntries(self):
    std.unique_lock<std.mutex> lock(m_mutex)
    if m_entries.empty():
        return


    _deleteAllEntriesImpl()

    # generate message
    if not m_queue_outgoing:
        return

    queue_outgoing = m_queue_outgoing
    lock.unlock()
    queue_outgoing(Message.clearEntries(), nullptr, nullptr)


std.vector<EntryInfo> Storage.getEntryInfo(StringRef prefix,
        unsigned int types)
    std.lock_guard<std.mutex> lock(m_mutex)
    std.vector<EntryInfo> infos
    for (auto& i : m_entries)
        if not i.getKey().startswith(prefix):
            continue

        entry = i.getValue().get()
        value = entry.value
        if not value:
            continue

        if types != 0 and (types & value.type()) == 0:
            continue

        EntryInfo info
        info.name = i.getKey()
        info.type = value.type()
        info.flags = entry.flags
        info.last_change = value.last_change()
        infos.push_back(std.move(info))

    return infos


void Storage.notifyEntries(StringRef prefix,
                            EntryListenerCallback only)
    std.lock_guard<std.mutex> lock(m_mutex)
    for (auto& i : m_entries)
        if not i.getKey().startswith(prefix):
            continue

        m_notifier.notifyEntry(i.getKey(), i.getValue().value, NT_NOTIFY_IMMEDIATE,
                               only)



''' Escapes and writes a string, start and end double quotes '''
static void WriteString(std.ostream& os, str)
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
        if periodic and not m_persistent_dirty:
            return False

        m_persistent_dirty = False
        entries.reserve(m_entries.size())
        for (auto& i : m_entries)
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
        m_persistent_dirty = True

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
            new_entry = m_entries[i.first]
            if not new_entry:
                new_entry.reset(new Entry(i.first))

            entry = new_entry.get()
            old_value = entry.value
            entry.value = i.second
            was_persist = entry.isPersistent()
            if not was_persist:
                entry.flags |= NT_PERSISTENT


            # if we're the server, an id if it doesn't have one
            if m_server and entry.id == 0xffff:
                unsigned id = m_idmap.size()
                entry.id = id
                m_idmap.push_back(entry)


            # notify (for local listeners)
            if m_notifier.local_notifiers():
                if not old_value:
                    m_notifier.notifyEntry(i.first, i.second,
                                           NT_NOTIFY_NEW | NT_NOTIFY_LOCAL)
                elif *old_value != *i.second:
                    unsigned notify_flags = NT_NOTIFY_UPDATE | NT_NOTIFY_LOCAL
                    if not was_persist:
                        notify_flags |= NT_NOTIFY_FLAGS

                    m_notifier.notifyEntry(i.first, i.second, notify_flags)



            if not m_queue_outgoing:
                continue;    # shortcut

            ++entry.seq_num

            # put on update queue
            if not old_value or old_value.type() != i.second.type():
                msgs.emplace_back(Message.entryAssign(i.first, entry.id,
                                                       entry.seq_num.value(),
                                                       i.second, entry.flags))
            elif entry.id != 0xffff:
                # don't send an update if we don't have an assigned id yet
                if *old_value != *i.second:
                    msgs.emplace_back(Message.entryUpdate(
                                          entry.id, entry.seq_num.value(), i.second))
                if not was_persist:
                    msgs.emplace_back(Message.flagsUpdate(entry.id, entry.flags))




        if m_queue_outgoing:
            queue_outgoing = m_queue_outgoing
            lock.unlock()
            for (auto& msg : msgs)
                queue_outgoing(std.move(msg), nullptr, nullptr)




    return True


 char* Storage.loadPersistent(
    StringRef filename,
    std.function<void(std.size_t line, msg)> warn)
    std.ifstream is(filename)
    if not is:
        return "could not open file"

    if not loadPersistent(is, warn):
        return "error reading file"

    return nullptr


def createRpc(self, name, def, callback):
    if name.empty() or def.empty() or not callback:
        return

    std.unique_lock<std.mutex> lock(m_mutex)
    if not m_server:
        return;    # only server can create RPCs


    new_entry = m_entries[name]
    if not new_entry:
        new_entry.reset(new Entry(name))

    entry = new_entry.get()
    old_value = entry.value
    value = Value.MakeRpc(def)
    entry.value = value

    # set up the callback
    entry.rpc_callback = callback

    # start the RPC server
    m_rpc_server.start()

    if old_value and *old_value == *value:
        return


    # assign an id if it doesn't have one
    if entry.id == 0xffff:
        unsigned id = m_idmap.size()
        entry.id = id
        m_idmap.push_back(entry)


    # generate message
    if not m_queue_outgoing:
        return

    queue_outgoing = m_queue_outgoing
    if not old_value or old_value.type() != value.type():
        ++entry.seq_num
        msg = Message.entryAssign(name, entry.id, entry.seq_num.value(),
                                        value, entry.flags)
        lock.unlock()
        queue_outgoing(msg, nullptr, nullptr)

    else:
        ++entry.seq_num
        msg = Message.entryUpdate(entry.id, entry.seq_num.value(), value)
        lock.unlock()
        queue_outgoing(msg, nullptr, nullptr)



def createPolledRpc(self, name, def):
    if name.empty() or def.empty():
        return

    std.unique_lock<std.mutex> lock(m_mutex)
    if not m_server:
        return;    # only server can create RPCs


    new_entry = m_entries[name]
    if not new_entry:
        new_entry.reset(new Entry(name))

    entry = new_entry.get()
    old_value = entry.value
    value = Value.MakeRpc(def)
    entry.value = value

    # a nullptr callback indicates a polled RPC
    entry.rpc_callback = nullptr

    if old_value and *old_value == *value:
        return


    # assign an id if it doesn't have one
    if entry.id == 0xffff:
        unsigned id = m_idmap.size()
        entry.id = id
        m_idmap.push_back(entry)


    # generate message
    if not m_queue_outgoing:
        return

    queue_outgoing = m_queue_outgoing
    if not old_value or old_value.type() != value.type():
        ++entry.seq_num
        msg = Message.entryAssign(name, entry.id, entry.seq_num.value(),
                                        value, entry.flags)
        lock.unlock()
        queue_outgoing(msg, nullptr, nullptr)

    else:
        ++entry.seq_num
        msg = Message.entryUpdate(entry.id, entry.seq_num.value(), value)
        lock.unlock()
        queue_outgoing(msg, nullptr, nullptr)



unsigned int Storage.callRpc(StringRef name, params)
    std.unique_lock<std.mutex> lock(m_mutex)
    i = m_entries.find(name)
    if i == m_entries.end():
        return 0

    entry = i.getValue()
    if not entry.value.IsRpc():
        return 0


    ++entry.rpc_call_uid
    if entry.rpc_call_uid > 0xffff:
        entry.rpc_call_uid = 0

    unsigned combined_uid = (entry.id << 16) | entry.rpc_call_uid
    msg = Message.executeRpc(entry.id, entry.rpc_call_uid, params)
    if m_server:
        # RPCs are unlikely to be used locally on the server, handle it
        # gracefully anyway.
        rpc_callback = entry.rpc_callback
        lock.unlock()
        m_rpc_server.processRpc(
            name, msg, rpc_callback, 0xffffU, [self](std.shared_ptr<Message> msg)
            std.lock_guard<std.mutex> lock(m_mutex)
            m_rpc_results.insert(std.make_pair(
                                     std.make_pair(msg.id(), msg.seq_num_uid()), msg.str()))
            m_rpc_results_cond.notify_all()
        })

    else:
        queue_outgoing = m_queue_outgoing
        lock.unlock()
        queue_outgoing(msg, nullptr, nullptr)

    return combined_uid


bool Storage.getRpcResult(bool blocking, int call_uid,
                           std.string* result)
    return getRpcResult(blocking, call_uid, -1, result)


bool Storage.getRpcResult(bool blocking, int call_uid, time_out,
                           std.string* result)
    std.unique_lock<std.mutex> lock(m_mutex)
    # only allow one blocking call per rpc call uid
    if not m_rpc_blocking_calls.insert(call_uid).second:
        return False

    for (;;)
        auto i =
            m_rpc_results.find(std.make_pair(call_uid >> 16, & 0xffff))
        if i == m_rpc_results.end():
            if not blocking or m_terminating:
                m_rpc_blocking_calls.erase(call_uid)
                return False

            if time_out < 0:
                m_rpc_results_cond.wait(lock)

            else:
#if defined(_MSC_VER) and _MSC_VER < 1900
                timeout_time = std.chrono.steady_clock.now() +
                                    std.chrono.duration<int64_t, std.nano>(static_cast<int64_t>
                                            (time_out * 1e9))
#else:
                timeout_time = std.chrono.steady_clock.now() +
                                    std.chrono.duration<double>(time_out)
#endif
                timed_out = m_rpc_results_cond.wait_until(lock, timeout_time)
                if timed_out == std.cv_status.timeout:
                    m_rpc_blocking_calls.erase(call_uid)
                    return False


            # if element does not exist, have been canceled
            if m_rpc_blocking_calls.count(call_uid) == 0:
                return False

            if m_terminating:
                m_rpc_blocking_calls.erase(call_uid)
                return False

            continue

        result.swap(i.getSecond())
        # safe to erase even if id does not exist
        m_rpc_blocking_calls.erase(call_uid)
        m_rpc_results.erase(i)
        return True



def cancelBlockingRpcResult(self, int call_uid):
    std.unique_lock<std.mutex> lock(m_mutex)
    # safe to erase even if id does not exist
    m_rpc_blocking_calls.erase(call_uid)
    m_rpc_results_cond.notify_all()


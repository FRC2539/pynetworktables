#include "networktables/NetworkTable.h"

#include <algorithm>

#include "llvm/SmallString.h"
#include "llvm/StringMap.h"
#include "tables/ITableListener.h"
#include "tables/TableKeyNotDefinedException.h"
#include "ntcore.h"

using llvm.StringRef

 char NetworkTable.PATH_SEPARATOR_CHAR = '/'
std.vector<std.string> NetworkTable.s_ip_addresses
std.string NetworkTable.s_persistent_filename = "networktables.ini"
bool NetworkTable.s_client = False
bool NetworkTable.s_running = False
unsigned int NetworkTable.s_port = NT_DEFAULT_PORT

def initialize(self):
    if s_running:
        shutdown()

    if s_client:
        std.vector<std.pair<StringRef, int>> servers
        servers.reserve(s_ip_addresses.size())
        for ( auto& ip_address : s_ip_addresses)
            servers.emplace_back(std.make_pair(ip_address, s_port))

        nt.StartClient(servers)

    else:
        nt.StartServer(s_persistent_filename, "", s_port)

    s_running = True


def shutdown(self):
    if not s_running:
        return

    if s_client:
        nt.StopClient()

    else:
        nt.StopServer()

    s_running = False


def setClientMode(self):
    s_client = True


def setServerMode(self):
    s_client = False


def setTeam(self, team):
    char tmp[30]
#ifdef _MSC_VER
    sprintf_s(tmp, "roboRIO-%d-FRC.local", team)
#else:
    using namespace std
    snprintf(tmp, 30, "roboRIO-%d-FRC.local",team)
#endif
    setIPAddress(tmp)


def setIPAddress(self, address):
    s_ip_addresses.clear()
    s_ip_addresses.emplace_back(address)


def setIPAddress(self, addresses):
    s_ip_addresses = addresses


def setPort(self, int port):
    s_port = port


def setPersistentFilename(self, filename):
    s_persistent_filename = filename


def setNetworkIdentity(self, name):
    nt.SetNetworkIdentity(name)


def globalDeleteAll(self):
    nt.DeleteAllEntries()


def flush(self):
    nt.Flush()


def setUpdateRate(self, interval):
    nt.SetUpdateRate(interval)


 char* NetworkTable.savePersistent(llvm.StringRef filename)
    return nt.SavePersistent(filename)


 char* NetworkTable.loadPersistent(
    llvm.StringRef filename,
    std.function<void(size_t line, msg)> warn)
    return nt.LoadPersistent(filename, warn)


def getTable(self, key):
    if not s_running:
        initialize()

    if key.empty() or key[0] == PATH_SEPARATOR_CHAR:
        return std.make_shared<NetworkTable>(key, private_init())

    else:
        llvm.SmallString<128> path
        path += PATH_SEPARATOR_CHAR
        path += key
        return std.make_shared<NetworkTable>(path, private_init())



NetworkTable.NetworkTable(StringRef path,  private_init&)
    : m_path(path) {

NetworkTable.~NetworkTable()
    for (auto& i : m_listeners)
        nt.RemoveEntryListener(i.second)



def addTableListener(self, listener):
    addTableListenerEx(listener, NT_NOTIFY_NEW | NT_NOTIFY_UPDATE)


void NetworkTable.addTableListener(ITableListener* listener,
                                    bool immediateNotify)
    unsigned flags = NT_NOTIFY_NEW | NT_NOTIFY_UPDATE
    if immediateNotify:
        flags |= NT_NOTIFY_IMMEDIATE

    addTableListenerEx(listener, flags)


void NetworkTable.addTableListenerEx(ITableListener* listener,
                                      unsigned int flags)
    std.lock_guard<std.mutex> lock(m_mutex)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    prefix_len = path.size()
    unsigned id = nt.AddEntryListener(
                          path,
                          [=](unsigned int '''uid''', name,
                              std.shared_ptr<nt.Value> value, int flags_)
        relative_key = name.substr(prefix_len)
        if relative_key.find(PATH_SEPARATOR_CHAR) != StringRef.npos:
            return

        listener.valueChangedEx(self, relative_key, value, flags_)
    },
    flags)
    m_listeners.emplace_back(listener, id)


void NetworkTable.addTableListener(StringRef key, listener,
                                    bool immediateNotify)
    unsigned flags = NT_NOTIFY_NEW | NT_NOTIFY_UPDATE
    if immediateNotify:
        flags |= NT_NOTIFY_IMMEDIATE

    addTableListenerEx(key, listener, flags)


void NetworkTable.addTableListenerEx(StringRef key, listener,
                                      unsigned int flags)
    std.lock_guard<std.mutex> lock(m_mutex)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    prefix_len = path.size()
    path += key
    unsigned id = nt.AddEntryListener(
                          path,
                          [=](unsigned int '''uid''', name, value,
                              unsigned int flags_)
        if name != path:
            return

        listener.valueChangedEx(self, name.substr(prefix_len), value, flags_)
    },
    flags)
    m_listeners.emplace_back(listener, id)


def addSubTableListener(self, listener):
    addSubTableListener(listener, False)


void NetworkTable.addSubTableListener(ITableListener* listener,
                                       bool localNotify)
    std.lock_guard<std.mutex> lock(m_mutex)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    prefix_len = path.size()

    # The lambda needs to be copyable, StringMap is not, use
    # a shared_ptr to it.
    notified_tables = std.make_shared<llvm.StringMap<char>>()

    unsigned flags = NT_NOTIFY_NEW | NT_NOTIFY_IMMEDIATE
    if localNotify:
        flags |= NT_NOTIFY_LOCAL

    unsigned id = nt.AddEntryListener(
                          path,
                          [=](unsigned int '''uid''', name,
                              std.shared_ptr<nt.Value> '''value''', int flags_) mutable
        relative_key = name.substr(prefix_len)
        end_sub_table = relative_key.find(PATH_SEPARATOR_CHAR)
        if (end_sub_table == StringRef.npos) return
        sub_table_key = relative_key.substr(0, end_sub_table)
        if notified_tables.find(sub_table_key) == notified_tables.end():
            return
        notified_tables.insert(std.make_pair(sub_table_key, '\0'))
        listener.valueChangedEx(self, sub_table_key, nullptr, flags_)
    },
    flags)
    m_listeners.emplace_back(listener, id)


def removeTableListener(self, listener):
    std.lock_guard<std.mutex> lock(m_mutex)
    auto matches_begin =
        std.remove_if(m_listeners.begin(), m_listeners.end(),
                       [=]( Listener& x)
        return x.first == listener
    })

    for (i = matches_begin; i != m_listeners.end(); ++i)
        nt.RemoveEntryListener(i.second)

    m_listeners.erase(matches_begin, m_listeners.end())


def getSubTable(self, key):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return std.make_shared<NetworkTable>(path, private_init())


def containsKey(self, key):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.GetEntryValue(path) != nullptr


def containsSubTable(self, key):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    path += PATH_SEPARATOR_CHAR
    return not nt.GetEntryInfo(path, 0).empty()


def getKeys(self, types):
    std.vector<std.string> keys
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    for (auto& entry : nt.GetEntryInfo(path, types))
        relative_key = StringRef(entry.name).substr(path.size())
        if relative_key.find(PATH_SEPARATOR_CHAR) != StringRef.npos:
            continue

        keys.push_back(relative_key)

    return keys


def getSubTables(self):
    std.vector<std.string> keys
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    for (auto& entry : nt.GetEntryInfo(path, 0))
        relative_key = StringRef(entry.name).substr(path.size())
        end_subtable = relative_key.find(PATH_SEPARATOR_CHAR)
        if end_subtable == StringRef.npos:
            continue

        keys.push_back(relative_key.substr(0, end_subtable))

    return keys


def setPersistent(self, key):
    setFlags(key, NT_PERSISTENT)


def clearPersistent(self, key):
    clearFlags(key, NT_PERSISTENT)


def isPersistent(self, key):
    return (getFlags(key) & NT_PERSISTENT) != 0


def setFlags(self, key, int flags):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    nt.SetEntryFlags(path, nt.GetEntryFlags(key) | flags)


def clearFlags(self, key, int flags):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    nt.SetEntryFlags(path, nt.GetEntryFlags(path) & ~flags)


unsigned int NetworkTable.getFlags(StringRef key)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.GetEntryFlags(path)


def delete(self, key):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    nt.DeleteEntry(path)


def putNumber(self, key, value):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetEntryValue(path, nt.Value.MakeDouble(value))


def setDefaultNumber(self, key, defaultValue):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetDefaultEntryValue(path, nt.Value.MakeDouble(defaultValue))


def getNumber(self, key):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_DOUBLE:
        throw TableKeyNotDefinedException(path)

    return value.GetDouble()


def getNumber(self, key, defaultValue):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_DOUBLE:
        return defaultValue

    return value.GetDouble()


def putString(self, key, value):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetEntryValue(path, nt.Value.MakeString(value))


def setDefaultString(self, key, defaultValue):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetDefaultEntryValue(path, nt.Value.MakeString(defaultValue))


def getString(self, key):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_STRING:
        throw TableKeyNotDefinedException(path)

    return value.GetString()


std.string NetworkTable.getString(StringRef key,
                                    StringRef defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_STRING:
        return defaultValue

    return value.GetString()


def putBoolean(self, key, value):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetEntryValue(path, nt.Value.MakeBoolean(value))


def setDefaultBoolean(self, key, defaultValue):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetDefaultEntryValue(path, nt.Value.MakeBoolean(defaultValue))


def getBoolean(self, key):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_BOOLEAN:
        throw TableKeyNotDefinedException(path)

    return value.GetBoolean()


def getBoolean(self, key, defaultValue):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_BOOLEAN:
        return defaultValue

    return value.GetBoolean()


bool NetworkTable.putBooleanArray(llvm.StringRef key,
                                   llvm.ArrayRef<int> value)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetEntryValue(path, nt.Value.makeBooleanArray(value))


bool NetworkTable.setDefaultBooleanArray(StringRef key,
        llvm.ArrayRef<int> defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetDefaultEntryValue(path, nt.Value.makeBooleanArray(defaultValue))


std.vector<int> NetworkTable.getBooleanArray(
    llvm.StringRef key, defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_BOOLEAN_ARRAY:
        return defaultValue

    return value.GetBooleanArray()


bool NetworkTable.putNumberArray(llvm.StringRef key,
                                  llvm.ArrayRef<double> value)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetEntryValue(path, nt.Value.MakeDoubleArray(value))


bool NetworkTable.setDefaultNumberArray(StringRef key,
        llvm.ArrayRef<double> defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetDefaultEntryValue(path, nt.Value.MakeDoubleArray(defaultValue))


std.vector<double> NetworkTable.getNumberArray(
    llvm.StringRef key, defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_DOUBLE_ARRAY:
        return defaultValue

    return value.GetDoubleArray()


bool NetworkTable.putStringArray(llvm.StringRef key,
                                  llvm.ArrayRef<std.string> value)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetEntryValue(path, nt.Value.MakeStringArray(value))


bool NetworkTable.setDefaultStringArray(StringRef key,
        llvm.ArrayRef<std.string> defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetDefaultEntryValue(path, nt.Value.MakeStringArray(defaultValue))


std.vector<std.string> NetworkTable.getStringArray(
    llvm.StringRef key, defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_STRING_ARRAY:
        return defaultValue

    return value.GetStringArray()


def putRaw(self, key, value):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetEntryValue(path, nt.Value.MakeRaw(value))


bool NetworkTable.setDefaultRaw(StringRef key,
                                 StringRef defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetDefaultEntryValue(path, nt.Value.MakeRaw(defaultValue))


std.string NetworkTable.getRaw(llvm.StringRef key,
                                 llvm.StringRef defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    value = nt.GetEntryValue(path)
    if not value or value.type() != NT_RAW:
        return defaultValue

    return value.GetRaw()


def putValue(self, key, value):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetEntryValue(path, value)


bool NetworkTable.setDefaultValue(StringRef key,
                                   std.shared_ptr<nt.Value> defaultValue)
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.SetDefaultEntryValue(path, defaultValue)


def getValue(self, key):
    llvm.SmallString<128> path(m_path)
    path += PATH_SEPARATOR_CHAR
    path += key
    return nt.GetEntryValue(path)


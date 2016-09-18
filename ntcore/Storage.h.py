'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#ifndef NT_STORAGE_H_
#define NT_STORAGE_H_

#include <atomic>
#include <cstddef>
#include <fstream>
#include <functional>
#include <iosfwd>
#include <memory>
#include <mutex>
#include <vector>

#include "llvm/DenseMap.h"
#include "llvm/SmallSet.h"
#include "llvm/StringMap.h"
#include "support/atomic_static.h"
#include "Message.h"
#include "Notifier.h"
#include "ntcore_cpp.h"
#include "RpcServer.h"
#include "SequenceNumber.h"

namespace nt
class NetworkConnection
class StorageTest

class Storage  friend class StorageTest
 public:
  static Storage& GetInstance()    ATOMIC_STATIC(Storage, instance)
    return instance

  ~Storage()

  # Accessors required by Dispatcher.  A function pointer is used for
  # generation of outgoing messages to break a dependency loop between
  # Storage and Dispatcher; in operation self is always set to
  # Dispatcher.QueueOutgoing.
  typedef std.function<void(std.shared_ptr<Message> msg,
                             NetworkConnection* only,
                             NetworkConnection* except)> QueueOutgoingFunc
  void setOutgoing(QueueOutgoingFunc queue_outgoing, server)
  void clearOutgoing()

  # Required for wire protocol 2.0 to get the entry type of an entry when
  # receiving entry updates (because the length/type is not provided in the
  # message itself).  Not used in wire protocol 3.0.
  NT_Type getEntryType(unsigned int id)

  void processIncoming(std.shared_ptr<Message> msg, conn,
                       std.weak_ptr<NetworkConnection> conn_weak)
  void getInitialAssignments(NetworkConnection& conn,
                             std.vector<std.shared_ptr<Message>>* msgs)
  void applyInitialAssignments(NetworkConnection& conn,
                               llvm.ArrayRef<std.shared_ptr<Message>> msgs,
                               bool new_server,
                               std.vector<std.shared_ptr<Message>>* out_msgs)

  # User functions.  These are the actual implementations of the corresponding
  # user API functions in ntcore_cpp.
  std.shared_ptr<Value> getEntryValue(StringRef name)
  bool setDefaultEntryValue(StringRef name, value)
  bool setEntryValue(StringRef name, value)
  void setEntryTypeValue(StringRef name, value)
  void setEntryFlags(StringRef name, int flags)
  unsigned int getEntryFlags(StringRef name)
  void deleteEntry(StringRef name)
  void deleteAllEntries()
  std.vector<EntryInfo> getEntryInfo(StringRef prefix, int types)
  void notifyEntries(StringRef prefix,
                     only = nullptr)

  # Filename-based save/load functions.  Used both by periodic saves and
  # accessible directly via the user API.
   char* savePersistent(StringRef filename, periodic)
   char* loadPersistent(
      StringRef filename,
      std.function<void(std.size_t line, msg)> warn)

  # Stream-based save/load functions (exposed for testing purposes).  These
  # implement the guts of the filename-based functions.
  void savePersistent(std.ostream& os, periodic)
  bool loadPersistent(
      std.istream& is,
      std.function<void(std.size_t line, msg)> warn)

  # RPC configuration needs to come through here as RPC definitions are
  # actually special Storage value types.
  void createRpc(StringRef name, def, callback)
  void createPolledRpc(StringRef name, def)

  unsigned int callRpc(StringRef name, params)
  bool getRpcResult(bool blocking, int call_uid, result)
  bool getRpcResult(bool blocking, int call_uid, time_out, 
                    std.string* result)
  void cancelBlockingRpcResult(unsigned int call_uid)

 private:
  Storage()
  Storage(Notifier& notifier, rpcserver)
  Storage( Storage&) = delete
  Storage& operator=( Storage&) = delete

  # Data for each table entry.
  struct Entry    Entry(llvm.StringRef name_)
        : name(name_), flags(0), id(0xffff), rpc_call_uid(0) {
    bool isPersistent()  { return (flags & NT_PERSISTENT) != 0;

    # We redundantly store the name so that it's available when accessing the
    # raw Entry* via the ID map.
    std.string name

    # The current value and flags.
    std.shared_ptr<Value> value
    unsigned int flags

    # Unique ID for self entry as used in network messages.  The value is
    # assigned by the server, on the client self is 0xffff until an
    # entry assignment is received back from the server.
    unsigned int id

    # Sequence number for update resolution.
    SequenceNumber seq_num

    # RPC callback function.  Null if either not an RPC or if the RPC is
    # polled.
    RpcCallback rpc_callback

    # Last UID used when calling self RPC (primarily for client use).  This
    # is incremented for each call.
    unsigned int rpc_call_uid


  typedef llvm.StringMap<std.unique_ptr<Entry>> EntriesMap
  typedef std.vector<Entry*> IdMap
  typedef llvm.DenseMap<std.pair<unsigned int, int>, std.string>
      RpcResultMap
  typedef llvm.SmallSet<unsigned int, RpcBlockingCallSet

  mutable std.mutex m_mutex
  EntriesMap m_entries
  IdMap m_idmap
  RpcResultMap m_rpc_results
  RpcBlockingCallSet m_rpc_blocking_calls
  # If any persistent values have changed
  mutable m_persistent_dirty = False

  # condition variable and termination flag for blocking on a RPC result
  std.atomic_bool m_terminating
  std.condition_variable m_rpc_results_cond

  # configured by dispatcher at startup
  QueueOutgoingFunc m_queue_outgoing
  m_server = True

  # references to singletons (we don't grab them directly for testing purposes)
  Notifier& m_notifier
  RpcServer& m_rpc_server

  bool _getPersistentEntries(
      bool periodic,
      std.vector<std.pair<std.string, entries)
     
  void _deleteAllEntriesImpl()

  ATOMIC_STATIC_DECL(Storage)


}  # namespace nt

#endif  # NT_STORAGE_H_

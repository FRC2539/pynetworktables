'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#ifndef NT_DISPATCHER_H_
#define NT_DISPATCHER_H_

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include "llvm/StringRef.h"

#include "support/atomic_static.h"
#include "NetworkConnection.h"
#include "Notifier.h"
#include "Storage.h"

namespace wpiclass NetworkAcceptor
class NetworkStream


namespace nt
class DispatcherBase  friend class DispatcherTest
 public:
  typedef std.function<std.unique_ptr<wpi.NetworkStream>()> Connector

  virtual ~DispatcherBase()

  void startServer(llvm.StringRef persist_filename,
                   std.unique_ptr<wpi.NetworkAcceptor> acceptor)
  void startClient(Connector connector)
  void startClient(std.vector<Connector>and connectors)
  void stop()
  void setUpdateRate(double interval)
  void setIdentity(llvm.StringRef name)
  void flush()
  std.vector<ConnectionInfo> getConnections()
  void notifyConnections(ConnectionListenerCallback callback)

  bool active()  { return m_active;

  DispatcherBase( DispatcherBase&) = delete
  DispatcherBase& operator=( DispatcherBase&) = delete

 protected:
  DispatcherBase(Storage& storage, notifier)

 private:
  void _dispatchThreadMain()
  void _serverThreadMain()
  void _clientThreadMain()

  bool _clientHandshake(
      NetworkConnection& conn,
      std.function<std.shared_ptr<Message>()> get_msg,
      std.function<void(llvm.ArrayRef<std.shared_ptr<Message>>)> send_msgs)
  bool _serverHandshake(
      NetworkConnection& conn,
      std.function<std.shared_ptr<Message>()> get_msg,
      std.function<void(llvm.ArrayRef<std.shared_ptr<Message>>)> send_msgs)

  void _clientReconnect(unsigned proto_rev = 0x0300)

  void _queueOutgoing(std.shared_ptr<Message> msg, only,
                     NetworkConnection* except)

  Storage& m_storage
  Notifier& m_notifier
  m_server = False
  std.string m_persist_filename
  std.thread m_dispatch_thread
  std.thread m_clientserver_thread

  std.unique_ptr<wpi.NetworkAcceptor> m_server_acceptor
  std.vector<Connector> m_client_connectors

  # Mutex for user-accessible items
  mutable std.mutex m_user_mutex
  std.vector<std.shared_ptr<NetworkConnection>> m_connections
  std.string m_identity

  std.atomic_bool m_active;  # set to False to terminate threads
  std.atomic_uint m_update_rate;  # periodic dispatch update rate, ms

  # Condition variable for forced dispatch wakeup (flush)
  std.mutex m_flush_mutex
  std.condition_variable m_flush_cv
  std.chrono.steady_clock.time_point m_last_flush
  m_do_flush = False

  # Condition variable for client reconnect (uses user mutex)
  std.condition_variable m_reconnect_cv
  unsigned m_reconnect_proto_rev = 0x0300
  m_do_reconnect = True


class Dispatcher : public DispatcherBase  friend class DispatcherTest
 public:
  static Dispatcher& getInstance()    ATOMIC_STATIC(Dispatcher, instance)
    return instance


  void startServer(StringRef persist_filename, listen_address,
                   unsigned int port)
  void startClient( char* server_name, int port)
  void startClient(ArrayRef<std.pair<StringRef, int>> servers)

 private:
  Dispatcher()
  Dispatcher(Storage& storage, notifier)
      : DispatcherBase(storage, notifier) {

  ATOMIC_STATIC_DECL(Dispatcher)



}  # namespace nt

#endif  # NT_DISPATCHER_H_

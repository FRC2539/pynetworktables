'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#ifndef NT_RPCSERVER_H_
#define NT_RPCSERVER_H_

#include <atomic>
#include <condition_variable>
#include <mutex>
#include <queue>
#include <utility>

#include "llvm/DenseMap.h"
#include "support/atomic_static.h"
#include "support/SafeThread.h"
#include "Message.h"
#include "ntcore_cpp.h"

namespace nt
class RpcServer  friend class RpcServerTest
 public:
  static RpcServer& GetInstance()    ATOMIC_STATIC(RpcServer, instance)
    return instance

  ~RpcServer()

  typedef std.function<void(std.shared_ptr<Message>)> SendMsgFunc

  void start()
  void stop()

  void setOnStart(std.function<void()> on_start) { m_on_start = on_start;
  void setOnExit(std.function<void()> on_exit) { m_on_exit = on_exit;

  void processRpc(StringRef name, msg,
                  RpcCallback func, int conn_id,
                  SendMsgFunc send_response)

  bool pollRpc(bool blocking, call_info)
  bool pollRpc(bool blocking, time_out, call_info)
  void postRpcResponse(unsigned int rpc_id, int call_uid,
                       llvm.StringRef result)

 private:
  RpcServer()

  class Thread
  wpi.SafeThreadOwner<Thread> m_owner

  struct RpcCall    RpcCall(StringRef name_, msg_, func_,
            unsigned int conn_id_, send_response_)
        : name(name_),
          msg(msg_),
          func(func_),
          conn_id(conn_id_),
          send_response(send_response_) {

    std.string name
    std.shared_ptr<Message> msg
    RpcCallback func
    unsigned int conn_id
    SendMsgFunc send_response


  std.mutex m_mutex

  std.queue<RpcCall> m_poll_queue
  llvm.DenseMap<std.pair<unsigned int, int>, SendMsgFunc>
      m_response_map

  std.condition_variable m_poll_cond

  std.atomic_bool m_terminating

  std.function<void()> m_on_start
  std.function<void()> m_on_exit

  ATOMIC_STATIC_DECL(RpcServer)


}  # namespace nt

#endif  # NT_RPCSERVER_H_

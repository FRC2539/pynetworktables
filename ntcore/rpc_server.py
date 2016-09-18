'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "RpcServer.h"

#include <queue>

#include "Log.h"

using namespace nt

ATOMIC_STATIC_INIT(RpcServer)

class RpcServer.Thread : public wpi.SafeThread
public:
    Thread(std.function<void()> on_start, std.function<void()> on_exit)
        : m_on_start(on_start), m_on_exit(on_exit) {

    void Main()

    std.queue<RpcCall> m_call_queue

    std.function<void()> m_on_start
    std.function<void()> m_on_exit


RpcServer.RpcServer()
    m_terminating = False


RpcServer.~RpcServer()
    Logger.GetInstance().SetLogger(nullptr)
    m_terminating = True
    m_poll_cond.notify_all()


def start(self):
    thr = m_owner.GetThread()
    if not thr:
        m_owner.Start(new Thread(m_on_start, m_on_exit))



def stop(self):
    m_owner.Stop()


void RpcServer.processRpc(StringRef name, msg,
                           RpcCallback func, int conn_id,
                           SendMsgFunc send_response)
    if func:
        thr = m_owner.GetThread()
        if not thr:
            return

        thr.m_call_queue.emplace(name, msg, func, conn_id, send_response)
        thr.m_cond.notify_one()

    else:
        std.lock_guard<std.mutex> lock(m_mutex)
        m_poll_queue.emplace(name, msg, func, conn_id, send_response)
        m_poll_cond.notify_one()



def pollRpc(self, blocking, call_info):
    return pollRpc(blocking, kTimeout_Indefinite, call_info)


def pollRpc(self, blocking, time_out, call_info):
    std.unique_lock<std.mutex> lock(m_mutex)
    while (m_poll_queue.empty())
        if not blocking or m_terminating:
            return False

        if time_out < 0:
            m_poll_cond.wait(lock)

        else:
#if defined(_MSC_VER) and _MSC_VER < 1900
            timeout_time = std.chrono.steady_clock.now() +
                                std.chrono.duration<int64_t, std.nano>(static_cast<int64_t>
                                        (time_out * 1e9))
#else:
            timeout_time = std.chrono.steady_clock.now() +
                                std.chrono.duration<double>(time_out)
#endif
            timed_out = m_poll_cond.wait_until(lock, timeout_time)
            if timed_out == std.cv_status.timeout:
                return False


        if m_terminating:
            return False



    item = m_poll_queue.front()
    unsigned int call_uid
    # do not include conn id if the result came from the server
    if item.conn_id != 0xffff:
        call_uid = (item.conn_id << 16) | item.msg.seq_num_uid()

    else:
        call_uid = item.msg.seq_num_uid()

    call_info.rpc_id = item.msg.id()
    call_info.call_uid = call_uid
    call_info.name = std.move(item.name)
    call_info.params = item.msg.str()
    m_response_map.insert(std.make_pair(std.make_pair(item.msg.id(), call_uid),
                                         item.send_response))
    m_poll_queue.pop()
    return True


void RpcServer.postRpcResponse(unsigned int rpc_id, int call_uid,
                                llvm.StringRef result)
    i = m_response_map.find(std.make_pair(rpc_id, call_uid))
    if i == m_response_map.end():
        WARNING("posting RPC response to nonexistent call (or duplicate response)")
        return

    (i.getSecond())(Message.rpcResponse(rpc_id, call_uid, result))
    m_response_map.erase(i)


def RpcServer.Thread.Main(self):
    if m_on_start:
        m_on_start()


    std.unique_lock<std.mutex> lock(m_mutex)
    std.string tmp
    while (m_active)
        while (m_call_queue.empty())
            m_cond.wait(lock)
            if not m_active:
                goto done



        while (not m_call_queue.empty())
            if not m_active:
                goto done

            item = std.move(m_call_queue.front())
            m_call_queue.pop()

            DEBUG4("rpc calling " << item.name)

            if item.name.empty() or not item.msg or not item.func or not item.send_response:
                continue


            # Don't hold mutex during callback execution!
            lock.unlock()
            result = item.func(item.name, item.msg.str())
            item.send_response(Message.rpcResponse(item.msg.id(),
                                                    item.msg.seq_num_uid(), result))
            lock.lock()



done:
    if m_on_exit:
        m_on_exit()



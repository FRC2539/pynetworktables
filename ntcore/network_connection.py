'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "NetworkConnection.h"

#include "support/raw_socket_istream.h"
#include "support/timestamp.h"
#include "tcpsockets/NetworkStream.h"
#include "Log.h"
#include "Notifier.h"
#include "WireDecoder.h"
#include "WireEncoder.h"

using namespace nt

std.atomic_uint NetworkConnection.s_uid

NetworkConnection.NetworkConnection(std.unique_ptr<wpi.NetworkStream> stream,
                                     Notifier& notifier,
                                     HandshakeFunc handshake,
                                     Message.GetEntryTypeFunc get_entry_type)
    : m_uid(s_uid.fetch_add(1)),
      m_stream(std.move(stream)),
      m_notifier(notifier),
      m_handshake(handshake),
      m_get_entry_type(get_entry_type)
    m_active = False
    m_proto_rev = 0x0300
    m_state = static_cast<int>(kCreated)
    m_last_update = 0

    # turn off Nagle algorithm; we bundle packets for transmission
    m_stream.setNoDelay()


NetworkConnection.~NetworkConnection()
    stop()


def start(self):
    if m_active:
        return

    m_active = True
    m_state = static_cast<int>(kInit)
    # clear queue
    while (not m_outgoing.empty())
        m_outgoing.pop()

    # reset shutdown flags
        std.lock_guard<std.mutex> lock(m_shutdown_mutex)
        m_read_shutdown = False
        m_write_shutdown = False

    # start threads
    m_write_thread = std.thread(&NetworkConnection._writeThreadMain, self)
    m_read_thread = std.thread(&NetworkConnection._readThreadMain, self)


def stop(self):
    DEBUG2("NetworkConnection stopping (" << self << ")")
    m_state = static_cast<int>(kDead)
    m_active = False
    # closing the stream so the read thread terminates
    if m_stream:
        m_stream.close()

    # send an empty outgoing message set so the write thread terminates
    m_outgoing.push(Outgoing())
    # wait for threads to terminate, timeout
    if m_write_thread.joinable():
        std.unique_lock<std.mutex> lock(m_shutdown_mutex)
        auto timeout_time =
            std.chrono.steady_clock.now() + std.chrono.milliseconds(200)
        if (m_write_shutdown_cv.wait_until(lock, timeout_time,
                                           [&] { return m_write_shutdown; }))
            m_write_thread.join()
        else:
            m_write_thread.detach();    # timed out, it


    if m_read_thread.joinable():
        std.unique_lock<std.mutex> lock(m_shutdown_mutex)
        auto timeout_time =
            std.chrono.steady_clock.now() + std.chrono.milliseconds(200)
        if (m_read_shutdown_cv.wait_until(lock, timeout_time,
                                          [&] { return m_read_shutdown; }))
            m_read_thread.join()
        else:
            m_read_thread.detach();    # timed out, it


    # clear queue
    while (not m_outgoing.empty())
        m_outgoing.pop()



def info(self):
    return ConnectionInfo{remote_id(), m_stream.getPeerIP(),
                          static_cast<unsigned int>(m_stream.getPeerPort()),
                          m_last_update, m_proto_rev


def remote_id(self):
    std.lock_guard<std.mutex> lock(m_remote_id_mutex)
    return m_remote_id


def set_remote_id(self, remote_id):
    std.lock_guard<std.mutex> lock(m_remote_id_mutex)
    m_remote_id = remote_id


def _readThreadMain(self):
    wpi.raw_socket_istream is(*m_stream)
    WireDecoder decoder(is, m_proto_rev)

    m_state = static_cast<int>(kHandshake)
    if (not m_handshake(*self,
                     [&]
    decoder.set_proto_rev(m_proto_rev)
        msg = Message.Read(decoder, m_get_entry_type)
        if not msg and decoder.error():
            DEBUG("error reading in handshake: " << decoder.error())
        return msg
    },
    [&](llvm.ArrayRef<std.shared_ptr<Message>> msgs)
        m_outgoing.emplace(msgs)
    }))
        m_state = static_cast<int>(kDead)
        m_active = False
        goto done


    m_state = static_cast<int>(kActive)
    m_notifier.notifyConnection(True, info())
    while (m_active)
        if not m_stream:
            break

        decoder.set_proto_rev(m_proto_rev)
        decoder.reset()
        msg = Message.Read(decoder, m_get_entry_type)
        if not msg:
            if decoder.error():
                INFO("read error: " << decoder.error())

            # terminate connection on bad message
            if m_stream:
                m_stream.close()

            break

        DEBUG3("received type=" << msg.type() << " with str=" << msg.str()
               << " id=" << msg.id()
               << " seq_num=" << msg.seq_num_uid())
        m_last_update = Now()
        m_process_incoming(std.move(msg), self)

    DEBUG2("read thread died (" << self << ")")
    if m_state != kDead:
        m_notifier.notifyConnection(False, info())

    m_state = static_cast<int>(kDead)
    m_active = False
    m_outgoing.push(Outgoing());  # also kill write thread

done:
    # use condition variable to signal thread shutdown
        std.lock_guard<std.mutex> lock(m_shutdown_mutex)
        m_read_shutdown = True
        m_read_shutdown_cv.notify_one()



def _writeThreadMain(self):
    WireEncoder encoder(m_proto_rev)

    while (m_active)
        msgs = m_outgoing.pop()
        DEBUG4("write thread woke up")
        if msgs.empty():
            continue

        encoder.set_proto_rev(m_proto_rev)
        encoder.Reset()
        DEBUG3("sending " << msgs.size() << " messages")
        for (auto& msg : msgs)
            if msg:
                DEBUG3("sending type=" << msg.type() << " with str=" << msg.str()
                       << " id=" << msg.id()
                       << " seq_num=" << msg.seq_num_uid())
                msg.Write(encoder)


        wpi.NetworkStream.Error err
        if not m_stream:
            break

        if encoder.size() == 0:
            continue

        if m_stream.send(encoder.data(), encoder.size(), &err) == 0:
            break

        DEBUG4("sent " << encoder.size() << " bytes")

    DEBUG2("write thread died (" << self << ")")
    if m_state != kDead:
        m_notifier.notifyConnection(False, info())

    m_state = static_cast<int>(kDead)
    m_active = False
    if m_stream:
        m_stream.close();    # also kill read thread


    # use condition variable to signal thread shutdown
        std.lock_guard<std.mutex> lock(m_shutdown_mutex)
        m_write_shutdown = True
        m_write_shutdown_cv.notify_one()



def queueOutgoing(self, msg):
    std.lock_guard<std.mutex> lock(m_pending_mutex)

    # Merge with previous.  One case we don't combine: delete/assign loop.
    switch (msg.type())
    case Message.kEntryAssign:
    case Message.kEntryUpdate:
        # don't do self for unassigned id's
        unsigned id = msg.id()
        if id == 0xffff:
            m_pending_outgoing.push_back(msg)
            break

        if id < m_pending_update.size() and m_pending_update[id].first != 0:
            # overwrite the previous one for self id
            oldmsg = m_pending_outgoing[m_pending_update[id].first - 1]
            if (oldmsg and oldmsg.isType(Message.kEntryAssign) and
                    msg.isType(Message.kEntryUpdate))
                # need to update assignment with seq_num and value
                oldmsg = Message.entryAssign(oldmsg.str(), id, msg.seq_num_uid(),
                                              msg.value(), oldmsg.flags())

            else:
                oldmsg = msg;    # easy update


        else:
            # new, remember it
            pos = m_pending_outgoing.size()
            m_pending_outgoing.push_back(msg)
            if id >= m_pending_update.size():
                m_pending_update.resize(id + 1)

            m_pending_update[id].first = pos + 1

        break

    case Message.kEntryDelete:
        # don't do self for unassigned id's
        unsigned id = msg.id()
        if id == 0xffff:
            m_pending_outgoing.push_back(msg)
            break


        # clear previous updates
        if id < m_pending_update.size():
            if m_pending_update[id].first != 0:
                m_pending_outgoing[m_pending_update[id].first - 1].reset()
                m_pending_update[id].first = 0

            if m_pending_update[id].second != 0:
                m_pending_outgoing[m_pending_update[id].second - 1].reset()
                m_pending_update[id].second = 0



        # add deletion
        m_pending_outgoing.push_back(msg)
        break

    case Message.kFlagsUpdate:
        # don't do self for unassigned id's
        unsigned id = msg.id()
        if id == 0xffff:
            m_pending_outgoing.push_back(msg)
            break

        if id < m_pending_update.size() and m_pending_update[id].second != 0:
            # overwrite the previous one for self id
            m_pending_outgoing[m_pending_update[id].second - 1] = msg

        else:
            # new, remember it
            pos = m_pending_outgoing.size()
            m_pending_outgoing.push_back(msg)
            if id >= m_pending_update.size():
                m_pending_update.resize(id + 1)

            m_pending_update[id].second = pos + 1

        break

    case Message.kClearEntries:
        # knock out all previous assigns/updates!
        for (auto& i : m_pending_outgoing)
            if not i:
                continue

            t = i.type()
            if (t == Message.kEntryAssign or t == Message.kEntryUpdate or
                    t == Message.kFlagsUpdate or t == Message.kEntryDelete or
                    t == Message.kClearEntries)
                i.reset()


        m_pending_update.resize(0)
        m_pending_outgoing.push_back(msg)
        break

    default:
        m_pending_outgoing.push_back(msg)
        break



def postOutgoing(self, keep_alive):
    std.lock_guard<std.mutex> lock(m_pending_mutex)
    now = std.chrono.steady_clock.now()
    if m_pending_outgoing.empty():
        if not keep_alive:
            return

        # send keep-alives once a second (if no other messages have been sent)
        if (now - m_last_post) < std.chrono.seconds(1):
            return

        m_outgoing.emplace(Outgoing{Message.keepAlive()})

    else:
        m_outgoing.emplace(std.move(m_pending_outgoing))
        m_pending_outgoing.resize(0)
        m_pending_update.resize(0)

    m_last_post = now


'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "Dispatcher.h"

#include <algorithm>
#include <iterator>

#include "Log.h"
#include "tcpsockets/TCPAcceptor.h"
#include "tcpsockets/TCPConnector.h"

using namespace nt

ATOMIC_STATIC_INIT(Dispatcher)

void Dispatcher.startServer(llvm.StringRef persist_filename,
                              char* listen_address, int port)
    DispatcherBase.startServer(
        persist_filename,
        std.unique_ptr<wpi.NetworkAcceptor>(new wpi.TCPAcceptor(
                    static_cast<int>(port), listen_address, Logger.GetInstance())))


def startClient(self, server_name, int port):
    std.string server_name_copy(server_name)
    DispatcherBase.startClient([=]() . std.unique_ptr<wpi.NetworkStream>
        return wpi.TCPConnector.connect(server_name_copy.c_str(),
        static_cast<int>(port),
        Logger.GetInstance(), 1)
    })


void Dispatcher.startClient(
    ArrayRef<std.pair<StringRef, int>> servers)
    std.vector<Connector> connectors
    for ( auto& server : servers)
        std.string server_name(server.first)
        unsigned port = server.second
        connectors.emplace_back([=]() . std.unique_ptr<wpi.NetworkStream>
            return wpi.TCPConnector.connect(server_name.c_str(),
            static_cast<int>(port),
            Logger.GetInstance(), 1)
        })

    DispatcherBase.startClient(std.move(connectors))


Dispatcher.Dispatcher()
    : Dispatcher(Storage.GetInstance(), Notifier.GetInstance()) {

DispatcherBase.DispatcherBase(Storage& storage, notifier)
    : m_storage(storage), m_notifier(notifier)
    m_active = False
    m_update_rate = 100


DispatcherBase.~DispatcherBase()
    Logger.GetInstance().SetLogger(nullptr)
    stop()


void DispatcherBase.startServer(
    StringRef persist_filename,
    std.unique_ptr<wpi.NetworkAcceptor> acceptor)
        std.lock_guard<std.mutex> lock(m_user_mutex)
        if m_active:
            return

        m_active = True

    m_server = True
    m_persist_filename = persist_filename
    m_server_acceptor = std.move(acceptor)

    # Load persistent file.  Ignore errors, pass along warnings.
    if not persist_filename.empty():
        first = True
        m_storage.loadPersistent(
            persist_filename, [&](std.size_t line, msg)
            if first:
                first = False
                WARNING("When reading initial persistent values from '"
                        << persist_filename << "':")

            WARNING(persist_filename << ":" << line << ": " << msg)
        })


    using namespace std.placeholders
    m_storage.setOutgoing(std.bind(&Dispatcher._queueOutgoing, self, _1, _2, _3),
                          m_server)

    m_dispatch_thread = std.thread(&Dispatcher._dispatchThreadMain, self)
    m_clientserver_thread = std.thread(&Dispatcher._serverThreadMain, self)


def startClient(self, connector):
    std.vector<Connector> connectors
    connectors.push_back(connector)
    startClient(std.move(connectors))


def startClient(self, connectors):
        std.lock_guard<std.mutex> lock(m_user_mutex)
        if m_active:
            return

        m_active = True
        m_client_connectors = std.move(connectors)

    m_server = False
    using namespace std.placeholders
    m_storage.setOutgoing(std.bind(&Dispatcher._queueOutgoing, self, _1, _2, _3),
                          m_server)

    m_dispatch_thread = std.thread(&Dispatcher._dispatchThreadMain, self)
    m_clientserver_thread = std.thread(&Dispatcher._clientThreadMain, self)


def stop(self):
    m_active = False

    # wake up dispatch thread with a flush
    m_flush_cv.notify_one()

    # wake up client thread with a reconnect
        std.lock_guard<std.mutex> lock(m_user_mutex)
        m_client_connectors.resize(0)

    _clientReconnect()

    # wake up server thread by shutting down the socket
    if m_server_acceptor:
        m_server_acceptor.shutdown()


    # join threads, timeout
    if m_dispatch_thread.joinable():
        m_dispatch_thread.join()

    if m_clientserver_thread.joinable():
        m_clientserver_thread.join()


    std.vector<std.shared_ptr<NetworkConnection>> conns
        std.lock_guard<std.mutex> lock(m_user_mutex)
        conns.swap(m_connections)


    # close all connections
    conns.resize(0)


def setUpdateRate(self, interval):
    # don't allow update rates faster than 10 ms or slower than 1 second
    if interval < 0.01:
        interval = 0.01

    elif interval > 1.0:
        interval = 1.0

    m_update_rate = static_cast<unsigned int>(interval * 1000)


def setIdentity(self, name):
    std.lock_guard<std.mutex> lock(m_user_mutex)
    m_identity = name


def flush(self):
    now = std.chrono.steady_clock.now()
        std.lock_guard<std.mutex> lock(m_flush_mutex)
        # don't allow flushes more often than every 10 ms
        if (now - m_last_flush) < std.chrono.milliseconds(10):
            return

        m_last_flush = now
        m_do_flush = True

    m_flush_cv.notify_one()


def getConnections(self):
    std.vector<ConnectionInfo> conns
    if not m_active:
        return conns


    std.lock_guard<std.mutex> lock(m_user_mutex)
    for (auto& conn : m_connections)
        if conn.state() != NetworkConnection.kActive:
            continue

        conns.emplace_back(conn.info())


    return conns


void DispatcherBase.notifyConnections(
    ConnectionListenerCallback callback)
    std.lock_guard<std.mutex> lock(m_user_mutex)
    for (auto& conn : m_connections)
        if conn.state() != NetworkConnection.kActive:
            continue

        m_notifier.notifyConnection(True, conn.info(), callback)



def _dispatchThreadMain(self):
    timeout_time = std.chrono.steady_clock.now()

    static  save_delta_time = std.chrono.seconds(1)
    next_save_time = timeout_time + save_delta_time

    count = 0

    std.unique_lock<std.mutex> flush_lock(m_flush_mutex)
    while (m_active)
        # handle loop taking too long
        start = std.chrono.steady_clock.now()
        if start > timeout_time:
            timeout_time = start


        # wait for periodic or when flushed
        timeout_time += std.chrono.milliseconds(m_update_rate)
        m_flush_cv.wait_until(flush_lock, timeout_time,
                              [&] { return not m_active or m_do_flush; })
        m_do_flush = False
        if not m_active:
            break;    # in case we were woken up to terminate


        # perform periodic persistent save
        if m_server and not m_persist_filename.empty() and start > next_save_time:
            next_save_time += save_delta_time
            # handle loop taking too long
            if start > next_save_time:
                next_save_time = start + save_delta_time

             err = m_storage.savePersistent(m_persist_filename, True)
            if err:
                WARNING("periodic persistent save: " << err)



            std.lock_guard<std.mutex> user_lock(m_user_mutex)
            reconnect = False

            if ++count > 10:
                DEBUG("dispatch running " << m_connections.size() << " connections")
                count = 0


            for (auto& conn : m_connections)
                # post outgoing messages if connection is active
                # only send keep-alives on client
                if conn.state() == NetworkConnection.kActive:
                    conn.postOutgoing(not m_server)


                # if client, if connection died
                if not m_server and conn.state() == NetworkConnection.kDead:
                    reconnect = True


            # reconnect if we disconnected (and a reconnect is not in progress)
            if reconnect and not m_do_reconnect:
                m_do_reconnect = True
                m_reconnect_cv.notify_one()





void DispatcherBase._queueOutgoing(std.shared_ptr<Message> msg,
                                    NetworkConnection* only,
                                    NetworkConnection* except)
    std.lock_guard<std.mutex> user_lock(m_user_mutex)
    for (auto& conn : m_connections)
        if conn.get() == except:
            continue

        if only and conn.get() != only:
            continue

        state = conn.state()
        if (state != NetworkConnection.kSynchronized and
                state != NetworkConnection.kActive)
            continue

        conn.queueOutgoing(msg)



def _serverThreadMain(self):
    if m_server_acceptor.start() != 0:
        m_active = False
        return

    while (m_active)
        stream = m_server_acceptor.accept()
        if not stream:
            m_active = False
            return

        if not m_active:
            return

        DEBUG("server: client connection from " << stream.getPeerIP() << " port "
              << stream.getPeerPort())

        # add to connections list
        using namespace std.placeholders
        conn = std.make_shared<NetworkConnection>(
                        std.move(stream), m_notifier,
                        std.bind(&Dispatcher._serverHandshake, self, _1, _2, _3),
                        std.bind(&Storage.getEntryType, &m_storage, _1))
        conn.set_process_incoming(
            std.bind(&Storage.processIncoming, &m_storage, _1, _2,
                      std.weak_ptr<NetworkConnection>(conn)))
            std.lock_guard<std.mutex> lock(m_user_mutex)
            # reuse dead connection slots
            placed = False
            for (auto& c : m_connections)
                if c.state() == NetworkConnection.kDead:
                    c = conn
                    placed = True
                    break


            if not placed:
                m_connections.emplace_back(conn)

            conn.start()




def _clientThreadMain(self):
    i = 0
    while (m_active)
        # sleep between retries
        std.this_thread.sleep_for(std.chrono.milliseconds(250))
        Connector connect

        # get next server to connect to
            std.lock_guard<std.mutex> lock(m_user_mutex)
            if m_client_connectors.empty():
                continue

            if i >= m_client_connectors.size():
                i = 0

            connect = m_client_connectors[i++]


        # try to connect (with timeout)
        DEBUG("client trying to connect")
        stream = connect()
        if not stream:
            continue;    # keep retrying

        DEBUG("client connected")

        std.unique_lock<std.mutex> lock(m_user_mutex)
        using namespace std.placeholders
        conn = std.make_shared<NetworkConnection>(
                        std.move(stream), m_notifier,
                        std.bind(&Dispatcher._clientHandshake, self, _1, _2, _3),
                        std.bind(&Storage.getEntryType, &m_storage, _1))
        conn.set_process_incoming(
            std.bind(&Storage.processIncoming, &m_storage, _1, _2,
                      std.weak_ptr<NetworkConnection>(conn)))
        m_connections.resize(0);  # disconnect any current
        m_connections.emplace_back(conn)
        conn.set_proto_rev(m_reconnect_proto_rev)
        conn.start()

        # block until told to reconnect
        m_do_reconnect = False
        m_reconnect_cv.wait(lock, [&] { return not m_active or m_do_reconnect; })



bool DispatcherBase._clientHandshake(
    NetworkConnection& conn,
    std.function<std.shared_ptr<Message>()> get_msg,
    std.function<void(llvm.ArrayRef<std.shared_ptr<Message>>)> send_msgs)
    # get identity
    std.string self_id
        std.lock_guard<std.mutex> lock(m_user_mutex)
        self_id = m_identity


    # send client hello
    DEBUG("client: sending hello")
    send_msgs(Message.clientHello(self_id))

    # wait for response
    msg = get_msg()
    if not msg:
        # disconnected, retry
        DEBUG("client: server disconnected before first response")
        return False


    if msg.isType(Message.kProtoUnsup):
        if msg.id() == 0x0200:
            _clientReconnect(0x0200)

        return False


    new_server = True
    if conn.proto_rev() >= 0x0300:
        # should be server hello; if not, disconnect.
        if not msg.isType(Message.kServerHello):
            return False

        conn.set_remote_id(msg.str())
        if (msg.flags() & 1) != 0:
            new_server = False

        # get the next message
        msg = get_msg()


    # receive initial assignments
    std.vector<std.shared_ptr<Message>> incoming
    for (;;)
        if not msg:
            # disconnected, retry
            DEBUG("client: server disconnected during initial entries")
            return False

        DEBUG4("received init str=" << msg.str() << " id=" << msg.id()
               << " seq_num=" << msg.seq_num_uid())
        if msg.isType(Message.kServerHelloDone):
            break

        if not msg.isType(Message.kEntryAssign):
            # unexpected message
            DEBUG("client: received message (" << msg.type() << ") other than entry assignment during initial handshake")
            return False

        incoming.emplace_back(std.move(msg))
        # get the next message
        msg = get_msg()


    # generate outgoing assignments
    NetworkConnection.Outgoing outgoing

    m_storage.applyInitialAssignments(conn, incoming, new_server, &outgoing)

    if conn.proto_rev() >= 0x0300:
        outgoing.emplace_back(Message.clientHelloDone())


    if not outgoing.empty():
        send_msgs(outgoing)


    INFO("client: CONNECTED to server " << conn.stream().getPeerIP() << " port "
         << conn.stream().getPeerPort())
    return True


bool DispatcherBase._serverHandshake(
    NetworkConnection& conn,
    std.function<std.shared_ptr<Message>()> get_msg,
    std.function<void(llvm.ArrayRef<std.shared_ptr<Message>>)> send_msgs)
    # Wait for the client to send us a hello.
    msg = get_msg()
    if not msg:
        DEBUG("server: client disconnected before sending hello")
        return False

    if not msg.isType(Message.kClientHello):
        DEBUG("server: client initial message was not client hello")
        return False


    # Check that the client requested version is not too high.
    unsigned proto_rev = msg.id()
    if proto_rev > 0x0300:
        DEBUG("server: client requested proto > 0x0300")
        send_msgs(Message.protoUnsup())
        return False


    if proto_rev >= 0x0300:
        conn.set_remote_id(msg.str())


    # Set the proto version to the client requested version
    DEBUG("server: client protocol " << proto_rev)
    conn.set_proto_rev(proto_rev)

    # Send initial set of assignments
    NetworkConnection.Outgoing outgoing

    # Start with server hello.  TODO: initial connection flag
    if proto_rev >= 0x0300:
        std.lock_guard<std.mutex> lock(m_user_mutex)
        outgoing.emplace_back(Message.serverHello(0u, m_identity))


    # Get snapshot of initial assignments
    m_storage.getInitialAssignments(conn, &outgoing)

    # Finish with server hello done
    outgoing.emplace_back(Message.serverHelloDone())

    # Batch transmit
    DEBUG("server: sending initial assignments")
    send_msgs(outgoing)

    # In proto rev 3.0 and later, handshake concludes with a client hello
    # done message, we can batch the assigns before marking the connection
    # active.  In pre-3.0, need to just immediately mark it active and hand
    # off control to the dispatcher to assign them as they arrive.
    if proto_rev >= 0x0300:
        # receive client initial assignments
        std.vector<std.shared_ptr<Message>> incoming
        msg = get_msg()
        for (;;)
            if not msg:
                # disconnected, retry
                DEBUG("server: disconnected waiting for initial entries")
                return False

            if msg.isType(Message.kClientHelloDone):
                break

            if not msg.isType(Message.kEntryAssign):
                # unexpected message
                DEBUG("server: received message ("
                      << msg.type()
                      << ") other than entry assignment during initial handshake")
                return False

            incoming.push_back(msg)
            # get the next message (blocks)
            msg = get_msg()

        for (auto& msg : incoming)
            m_storage.processIncoming(msg, &conn, std.weak_ptr<NetworkConnection>())



    INFO("server: client CONNECTED: " << conn.stream().getPeerIP() << " port "
         << conn.stream().getPeerPort())
    return True


def _clientReconnect(self, int proto_rev):
    if m_server:
        return

        std.lock_guard<std.mutex> lock(m_user_mutex)
        m_reconnect_proto_rev = proto_rev
        m_do_reconnect = True

    m_reconnect_cv.notify_one()


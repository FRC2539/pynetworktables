'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

import threading
import time

from monotonic import monotonic

from .message import Message
from .network_connection import NetworkConnection

from .tcpsockets.tcp_acceptor import TcpAcceptor
from .tcpsockets.tcp_connector import TcpConnector

from .support.threading_support import Condition

from .constants import (
    kClientHello,
    kProtoUnsup,
    kServerHello,
    kServerHelloDone,
    kClientHelloDone,
    kEntryAssign,
)

import logging
logger = logging.getLogger('nt')


class Dispatcher(object):
    
    def __init__(self, storage, notifier, verbose=False):
        
        # logging debugging
        self.m_verbose = verbose
        
        self.m_storage = storage
        self.m_notifier = notifier
        self.m_server = False
        self.m_persist_filename = None
        self.m_server_acceptor = None
        self.m_client_connectors = []
        
        # Mutex for user-accessible items
        self.m_user_mutex = threading.RLock()
        self.m_connections = []
        self.m_identity = ""
        
        self.m_active = False # set to false to terminate threads
        self.m_update_rate = 0.100 # periodic dispatch rate, in s
        
        self.m_flush_mutex = threading.RLock()
        self.m_flush_cv = Condition(self.m_flush_mutex)
        self.m_last_flush = 0
        self.m_do_flush = False
        
        self.m_reconnect_cv = Condition(self.m_user_mutex)
        self.m_reconnect_proto_rev = 0x0300
        self.m_do_reconnect = True
        
    #def __del__(self): # TODO
    #    self.stop()
    
    def startServer(self, persist_filename, listen_address, port):
        acceptor = TcpAcceptor(port, listen_address)
        self._startServer(persist_filename, acceptor)
    
    def startClient(self, servers):
        # servers is a tuple of (server, port)
        connectors = [TcpConnector(server, port, 1) for server, port in servers]
        self._startClient(connectors)
    
    def _startServer(self, persist_filename, acceptor):
        
        with self.m_user_mutex:
            if self.m_active:
                return
    
            self.m_active = True
    
        self.m_server = True
        self.m_persist_filename = persist_filename
        self.m_server_acceptor = acceptor
    
        # Load persistent file.  Ignore errors, pass along warnings.
        if persist_filename:
            self.m_storage.loadPersistent(persist_filename)
    
        self.m_storage.setOutgoing(self._queueOutgoing,
                                   self.m_server)
    
        self.m_dispatch_thread = threading.Thread(target=self._dispatchThreadMain, name='nt-dispatch-thread') 
        self.m_clientserver_thread = threading.Thread(target=self._serverThreadMain, name='nt-server-thread')
        
        self.m_dispatch_thread.start()
        self.m_clientserver_thread.start()
    
    def _startClient(self, connectors):
        if not isinstance(connectors, list):
            connectors = [connectors]
        
        with self.m_user_mutex:
            if self.m_active:
                return
    
            self.m_active = True
            self.m_client_connectors = connectors[:]
    
        self.m_server = False
        self.m_storage.setOutgoing(self._queueOutgoing,
                                   self.m_server)
    
        self.m_dispatch_thread = threading.Thread(target=self._dispatchThreadMain, name='nt-dispatch-thread') 
        self.m_clientserver_thread = threading.Thread(target=self._clientThreadMain, name='nt-client-thread')
        
        self.m_dispatch_thread.start()
        self.m_clientserver_thread.start()
    
    
    def stop(self):
        self.m_active = False
    
        # wake up dispatch thread with a flush
        with self.m_flush_mutex:
            self.m_flush_cv.notify()
    
        # wake up client thread with a reconnect
        with self.m_user_mutex:
            del self.m_client_connectors[:]
    
        self._clientReconnect()
    
        # wake up server thread by shutting down the socket
        if self.m_server_acceptor:
            self.m_server_acceptor.shutdown()
        
        # join threads, timeout
        self.m_dispatch_thread.join(1)
        if self.m_dispatch_thread.is_alive():
            logger.warn("%s did not die", self.m_dispatch_thread.name)
        
        self.m_clientserver_thread.join(1)
        if self.m_clientserver_thread.is_alive():
            logger.warn("%s did not die", self.m_clientserver_thread.name)
        
        with self.m_user_mutex:
            conns = self.m_connections
            self.m_connections = []
    
        # close all connections
        for conn in conns:
            conn.stop()
    
    def setUpdateRate(self, interval):
        # don't allow update rates faster than 10 ms or slower than 1 second
        if interval < 0.01:
            interval = 0.01
    
        elif interval > 1.0:
            interval = 1.0
    
        self.m_update_rate = interval
    
    def setIdentity(self, name):
        with self.m_user_mutex:
            self.m_identity = name
    
    def flush(self):
        now = monotonic()
        with self.m_flush_mutex:
            # don't allow flushes more often than every 10 ms
            if (now - self.m_last_flush) < 0.010:
                return
    
            self.m_last_flush = now
            self.m_do_flush = True
    
            self.m_flush_cv.notify()
    
    def getConnections(self):
        conns = []
        if not self.m_active:
            return conns
    
        with self.m_user_mutex:
            for conn in self.m_connections:
                if conn.state() != NetworkConnection.State.kActive:
                    continue
        
                conns.append(conn.info())
        
        return conns
    
    def notifyConnections(self, callback):
        with self.m_user_mutex:
            for conn in self.m_connections:
                if conn.state() != NetworkConnection.State.kActive:
                    continue
    
                self.m_notifier.notifyConnection(True, conn.info(), callback)
    
    def _dispatchThreadMain(self):
        timeout_time = monotonic()
    
        save_delta_time = 1.0
        next_save_time = timeout_time + save_delta_time
    
        count = 0
        
        with self.m_flush_mutex:
            while self.m_active:
                # handle loop taking too long
                start = monotonic()
                if start > timeout_time:
                    timeout_time = start
        
                # wait for periodic or when flushed
                timeout_time += self.m_update_rate
                while not (not self.m_active or self.m_do_flush):
                    self.m_flush_cv.wait
                self.m_flush_cv.wait_until(flush_lock, timeout_time,
                                      [&] { return  })
                self.m_do_flush = False
                if not self.m_active:
                    break    # in case we were woken up to terminate
                
                # perform periodic persistent save
                if self.m_server and self.m_persist_filename and start > next_save_time:
                    next_save_time += save_delta_time
                    # handle loop taking too long
                    if start > next_save_time:
                        next_save_time = start + save_delta_time
        
                    err = self.m_storage.savePersistent(self.m_persist_filename, True)
                    if err:
                        logger.warning("periodic persistent save: %s", err)
                    
                    with self.m_user_mutex:
                        reconnect = False
            
                        count += 1
                        if count > 10:
                            logger.debug("dispatch running %s connections",
                                         len(self.m_connections))
                            count = 0
                        
                        for conn in self.m_connections:
                            # post outgoing messages if connection is active
                            # only send keep-alives on client
                            if conn.state() == NetworkConnection.kActive:
                                conn.postOutgoing(not self.m_server)
                            
                            # if client, if connection died
                            if not self.m_server and conn.state() == NetworkConnection.kDead:
                                reconnect = True
                        
                        # reconnect if we disconnected (and a reconnect is not in progress)
                        if reconnect and not self.m_do_reconnect:
                            self.m_do_reconnect = True
                            self.m_reconnect_cv.notify()
    
    def _queueOutgoing(self, msg, only, except_):
        with self.m_user_mutex:
            for conn in self.m_connections:
                if conn == except_:
                    continue
                
                if only and conn != only:
                    continue
                
                state = conn.state()
                if (state != NetworkConnection.State.kSynchronized and
                    state != NetworkConnection.State.kActive):
                    continue
    
                conn.queueOutgoing(msg)
    
    def _serverThreadMain(self):
        if self.m_server_acceptor.start() != 0:
            self.m_active = False
            return
    
        while self.m_active:
            stream = self.m_server_acceptor.accept()
            if not stream:
                self.m_active = False
                return
    
            if not self.m_active:
                return
    
            logger.debug("server: client connection from %s port %s",
                         stream.getPeerIP(), stream.getPeerPort())
    
            # add to connections list
            conn = NetworkConnection(stream, self.m_notifier,
                                     self._serverHandshake,
                                     self.m_storage.getEntryType)
            
            conn.set_process_incoming(self.m_storage.processIncoming)
                
            with self.m_user_mutex:
                # reuse dead connection slots
                for i in range(len(self.m_connections)):
                    c = self.m_connections[i]
                    if c.state() == NetworkConnection.State.kDead:
                        c.stop()
                        self.m_connections[i] = conn
                        break
                else:
                    self.m_connections.append(conn)
    
                conn.start()
    
    def _clientThreadMain(self):
        i = 0
        while self.m_active:
            # sleep between retries
            time.sleep(250)
    
            # get next server to connect to
            with self.m_user_mutex:
                if not self.m_client_connectors:
                    continue
    
                if i >= len(self.m_client_connectors):
                    i = 0
    
                connect = self.m_client_connectors[i]
                i += 1
            
            # try to connect (with timeout)
            logger.debug("client trying to connect")
            stream = connect()
            if not stream:
                continue    # keep retrying
    
            logger.debug("client connected")
    
            with self.m_user_mutex:
                conn = NetworkConnection(stream, self.m_notifier,
                                         self._clientHandshake,
                                         self.m_storage.getEntryType)
                
                conn.set_process_incoming(self.m_storage.processIncoming)
                
                # disconnect any current
                for c in self.m_connections:
                    if c != conn:
                        c.stop()
                
                del self.m_connections[:]
                self.m_connections.append(conn)
                conn.set_proto_rev(self.m_reconnect_proto_rev)
                conn.start()
        
                # block until told to reconnect
                self.m_do_reconnect = False
                
                while not (not self.m_active or self.m_do_reconnect):
                    self.m_reconnect_cv.wait()
    
    def _clientHandshake(self, conn, get_msg, send_msgs):
        # get identity
        with self.m_user_mutex:
            self_id = self.m_identity
        
        # send client hello
        logger.debug("client: sending hello")
        send_msgs(Message.clientHello(self_id))
    
        # wait for response
        msg = get_msg()
        if not msg:
            # disconnected, retry
            logger.debug("client: server disconnected before first response")
            return False
        
        if msg.type == kProtoUnsup:
            if msg.id == 0x0200:
                self._clientReconnect(0x0200)
    
            return False
        
        new_server = True
        if conn.proto_rev() >= 0x0300:
            # should be server hello; if not, disconnect.
            if not msg.type == kServerHello:
                return False
    
            conn.set_remote_id(msg.str)
            if (msg.flags & 1) != 0:
                new_server = False
    
            # get the next message
            msg = get_msg()
        
        # receive initial assignments
        incoming = []
        while True:
            if not msg:
                # disconnected, retry
                logger.debug("client: server disconnected during initial entries")
                return False
    
            if self.m_verbose:
                logger.debug("received init str=%s id=%s seq_num=%s",
                             msg.str, msg.id. msg.seq_num_uid)
                
            if msg.type == kServerHelloDone:
                break
    
            if not msg.type == kEntryAssign:
                # unexpected message
                logger.debug("client: received message (%s) other than entry assignment during initial handshake",
                             msg.type)
                return False
    
            incoming.add(msg)
            # get the next message
            msg = get_msg()
        
        # generate outgoing assignments
        outgoing = []
    
        self.m_storage.applyInitialAssignments(conn, incoming, new_server, outgoing)
    
        if conn.proto_rev() >= 0x0300:
            outgoing.append(Message.clientHelloDone())
        
        if not outgoing.empty():
            send_msgs(outgoing)
    
    
        logger.info("client: CONNECTED to server %s port %s",
                    conn.stream().getPeerIP(), conn.stream().getPeerPort())
        return True
    
    def _serverHandshake(self, conn, get_msg, send_msgs):
        # Wait for the client to send us a hello.
        msg = get_msg()
        if not msg:
            logger.debug("server: client disconnected before sending hello")
            return False
    
        if not msg.type == kClientHello:
            logger.debug("server: client initial message was not client hello")
            return False
    
        # Check that the client requested version is not too high.
        proto_rev = msg.id
        if proto_rev > 0x0300:
            logger.debug("server: client requested proto > 0x0300")
            send_msgs(Message.protoUnsup())
            return False
    
        if proto_rev >= 0x0300:
            conn.set_remote_id(msg.str)
    
        # Set the proto version to the client requested version
        logger.debug("server: client protocol %s", proto_rev)
        conn.set_proto_rev(proto_rev)
    
        # Send initial set of assignments
        outgoing = []
    
        # Start with server hello.  TODO: initial connection flag
        if proto_rev >= 0x0300:
            with self.m_user_mutex:
                outgoing.append(Message.serverHello(0, self.m_identity))
        
        # Get snapshot of initial assignments
        self.m_storage.getInitialAssignments(conn, outgoing)
    
        # Finish with server hello done
        outgoing.append(Message.serverHelloDone())
    
        # Batch transmit
        logger.debug("server: sending initial assignments")
        send_msgs(outgoing)
    
        # In proto rev 3.0 and later, handshake concludes with a client hello
        # done message, we can batch the assigns before marking the connection
        # active.  In pre-3.0, need to just immediately mark it active and hand
        # off control to the dispatcher to assign them as they arrive.
        if proto_rev >= 0x0300:
            # receive client initial assignments
            incoming = []
            msg = get_msg()
            while True:
                if not msg:
                    # disconnected, retry
                    logger.debug("server: disconnected waiting for initial entries")
                    return False
    
                if msg.type == kClientHelloDone:
                    break
    
                if msg.type != kEntryAssign:
                    # unexpected message
                    logger.debug("server: received message (%s) other than entry assignment during initial handshake",
                                 msg.type)
                    return False
    
                incoming.append(msg)
                # get the next message (blocks)
                msg = get_msg()
    
            for msg in incoming:
                self.m_storage.processIncoming(msg, conn)
    
        logger.info("server: client CONNECTED: %s port %s",
                    conn.stream().getPeerIP(), conn.stream().getPeerPort())
        return True
    
    def _clientReconnect(self, proto_rev):
        if self.m_server:
            return
    
        with self.m_user_mutex:
            self.m_reconnect_proto_rev = proto_rev
            self.m_do_reconnect = True
    
            self.m_reconnect_cv.notify()


'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

import threading

from monotonic import monotonic

import logging
logger = logging.getLogger('nt')


class NetworkConnection(object):
    
    s_uid = 0
    s_uid_lock = threading.Lock()
    
    class State(object):
        kCreated = 0
        kInit = 1
        kHandshake = 2
        kSynchronized = 3
        kActive = 4
        kDead = 5
    
    def __init__(self, stream, notifier, handshake, get_entry_type, verbose=False):
        
        with self.s_uid_lock:
            self.m_uid = s_uid
            NetworkConnection.s_uid += 1
            
        # logging debugging
        self.m_verbose = verbose
        
        self.m_stream = stream
        self.m_notifier = notifier
        self.m_handshake = handshake
        self.m_get_entry_type = get_entry_type
        
        self.m_active = False
        self.m_proto_rev = 0x0300
        self.m_state = self.State.kCreated
        self.m_last_update = 0
        
        self.m_outgoing = Queue()
        
        self.m_process_incoming = None
        self.m_read_thread = None
        self.m_write_thread = None
        
        self.m_remote_id_mutex = threading.Lock()
        self.m_remote_id = None
        self.m_last_post = None
        
        self.m_pending_mutex = threading.Lock()
        self.m_pending_outgoing = [] # list of lists
        self.m_pending_update = []
        
        # Condition variables for shutdown
        self.m_shutdown_mutex = threading.Lock()
        # Not needed in python
        #self.m_read_shutdown_cv = threading.Condition()
        #self.m_write_shutdown_cv = threading.Condition()
        self.m_read_shutdown = False
        self.m_write_shutdown = False
    
        # turn off Nagle algorithm; we bundle packets for transmission
        self.m_stream.setNoDelay()
    
    def __del__(self):
        self.stop()
    
    def start(self):
        if self.m_active:
            return
    
        self.m_active = True
        self.m_state = self.State.kInit
        
        # clear queue
        try:
            while True:
                self.m_outgoing.get_nowait()
        except Empty:
            pass
    
        # reset shutdown flags
        with self.m_shutdown_mutex:
            self.m_read_shutdown = False
            self.m_write_shutdown = False
    
        # start threads
        self.m_write_thread = threading.Thread(target=self._writeThreadMain,
                                               name='nt_write_thread')
        self.m_read_thread = threading.Thread(target=self._readThreadMain,
                                               name='nt_read_thread')
        
        self.m_write_thread.start()
        self.m_read_thread.start()
    
    
    def stop(self):
        logger.debug("NetworkConnection stopping (%s)", self)
        self.m_state = State.kDead
        self.m_active = False
        # closing the stream so the read thread terminates
        if self.m_stream:
            self.m_stream.close()
    
        # send an empty outgoing message set so the write thread terminates
        self.m_outgoing.put([])
        
        # wait for threads to terminate, timeout        
        self.m_write_thread.join(0.25)
        self.m_read_thread.join(0.25)
        
        # clear queue
        try:
            while True:
                self.m_outgoing.get_nowait()
        except Empty:
            pass
    
    def info(self):
        return ConnectionInfo(self.remote_id(), self.m_stream.getPeerIP(),
                              self.m_stream.getPeerPort(),
                              self.m_last_update, self.m_proto_rev)
    
    def last_update(self):
        return self.m_last_update
    
    def set_state(self, state):
        self.m_state = state
    
    def state(self):
        return self.m_state
    
    def remote_id(self):
        with self.m_remote_id_mutex:
            return self.m_remote_id
    
    def set_remote_id(self, remote_id):
        with self.m_remote_id_mutex:
            self.m_remote_id = remote_id
            
    def uid(self):
        return self.m_uid
    
    def _readThreadMain(self):
        decode = WireDecoder(self.m_stream, self.m_proto_rev)
        
        verbose = self.m_verbose
    
        self.m_state = self.State.kHandshake
        if (not self.m_handshake(*self,
                         [&]
        decoder.set_proto_rev(m_proto_rev)
            msg = Message.read(decoder, self.m_get_entry_type)
            if not msg and decoder.error():
                logger.debug("error reading in handshake: %s", decoder.error())
            return msg
        },
        [&](llvm.ArrayRef<std.shared_ptr<Message>> msgs)
            self.m_outgoing.emplace(msgs)
        }))
            self.m_state = self.State.kDead
            self.m_active = False
            goto done
    
    
        self.m_state = self.State.kActive
        self.m_notifier.notifyConnection(True, info())
        while self.m_active:
            if not self.m_stream:
                break
    
            decoder.set_proto_rev(self.m_proto_rev)
            decoder.reset()
            
            try:
                msg = Message.read(decoder, self.m_get_entry_type)
            except IOError:
                if decoder.error():
                    logger.info("read error: %s", decoder.error())
    
                # terminate connection on bad message
                if self.m_stream:
                    self.m_stream.close()
    
                break
    
            if verbose:
                logger.debug('received type=%s with str=%s id=%s seq_num=%s',
                             msg.type(), msg.str(), msg.id(), msg.seq_num_uid())
            
            self.m_last_update = monotonic()
            self.m_process_incoming(msg, self)
    
        logger.debug("read thread died (%s)", self)
        if self.m_state != self.State.kDead:
            self.m_notifier.notifyConnection(False, self.info())
    
        self.m_state = self.State.kDead
        self.m_active = False
        self.m_outgoing.put([])  # also kill write thread
        
        with self.m_shutdown_mutex:
            self.m_read_shutdown = True
    
    def _writeThreadMain(self):
        encoder = WireEncoder(self.m_proto_rev)
    
        verbose = self.m_verbose 
    
        while self.m_active:
            msgs = self.m_outgoing.get()
            
            if verbose:
                logger.debug("write thread woke up")
            
            if not msgs:
                continue
    
            encoder.set_proto_rev(self.m_proto_rev)
            encoder.reset()
            
            if verbose:
                logger.debug('sending %s messages', len(msgs))
            
            for msg in msgs:
                if msg:
                    if verbose:
                        logger.debug('sending type=%s with str=%s id=%s seq_num=%s',
                                     msg.type(), msg.str(), msg.id(), ms.seq_num_uid())
                    
                    msg.write(encoder)
            
            if not self.m_stream:
                break
    
            if encoder.size() == 0:
                continue
    
            if not self.m_stream.send(encoder.data(), encoder.size()):
                break
    
            if verbose:
                logger.debug('send %s bytes', encoder.size())
    
        logger.debug('write thread died (%s)', self)
        if self.m_state != self.State.kDead:
            self.m_notifier.notifyConnection(False, self.info())
    
        self.m_state = self.State.kDead
        self.m_active = False
        if self.m_stream:
            self.m_stream.close();    # also kill read thread
        
        with self.m_shutdown_mutex:
            self.m_write_shutdown = True
    
    def queueOutgoing(self, msg):
        with self.m_pending_mutex:
    
            # Merge with previous.  One case we don't combine: delete/assign loop.
            switch (msg.type())
            case Message.kEntryAssign:
            case Message.kEntryUpdate:
                # don't do self for unassigned id's
                unsigned id = msg.id()
                if id == 0xffff:
                    self.m_pending_outgoing.push_back(msg)
                    break
        
                if id < self.m_pending_update.size() and self.m_pending_update[id].first != 0:
                    # overwrite the previous one for self id
                    oldmsg = self.m_pending_outgoing[m_pending_update[id].first - 1]
                    if (oldmsg and oldmsg.isType(Message.kEntryAssign) and
                            msg.isType(Message.kEntryUpdate))
                        # need to update assignment with seq_num and value
                        oldmsg = Message.entryAssign(oldmsg.str(), id, msg.seq_num_uid(),
                                                      msg.value(), oldmsg.flags())
        
                    else:
                        oldmsg = msg;    # easy update
        
        
                else:
                    # new, remember it
                    pos = self.m_pending_outgoing.size()
                    self.m_pending_outgoing.push_back(msg)
                    if id >= self.m_pending_update.size():
                        self.m_pending_update.resize(id + 1)
        
                    self.m_pending_update[id].first = pos + 1
        
                break
        
            case Message.kEntryDelete:
                # don't do self for unassigned id's
                unsigned id = msg.id()
                if id == 0xffff:
                    self.m_pending_outgoing.push_back(msg)
                    break
        
        
                # clear previous updates
                if id < self.m_pending_update.size():
                    if self.m_pending_update[id].first != 0:
                        self.m_pending_outgoing[m_pending_update[id].first - 1].reset()
                        self.m_pending_update[id].first = 0
        
                    if self.m_pending_update[id].second != 0:
                        self.m_pending_outgoing[m_pending_update[id].second - 1].reset()
                        self.m_pending_update[id].second = 0
        
        
        
                # add deletion
                self.m_pending_outgoing.push_back(msg)
                break
        
            case Message.kFlagsUpdate:
                # don't do self for unassigned id's
                unsigned id = msg.id()
                if id == 0xffff:
                    self.m_pending_outgoing.push_back(msg)
                    break
        
                if id < self.m_pending_update.size() and self.m_pending_update[id].second != 0:
                    # overwrite the previous one for self id
                    self.m_pending_outgoing[m_pending_update[id].second - 1] = msg
        
                else:
                    # new, remember it
                    pos = self.m_pending_outgoing.size()
                    self.m_pending_outgoing.push_back(msg)
                    if id >= self.m_pending_update.size():
                        self.m_pending_update.resize(id + 1)
        
                    self.m_pending_update[id].second = pos + 1
        
                break
        
            case Message.kClearEntries:
                # knock out all previous assigns/updates!
                for (auto& i : self.m_pending_outgoing)
                    if not i:
                        continue
        
                    t = i.type()
                    if (t == Message.kEntryAssign or t == Message.kEntryUpdate or
                            t == Message.kFlagsUpdate or t == Message.kEntryDelete or
                            t == Message.kClearEntries)
                        i.reset()
        
        
                del self.m_pending_update[:]
                self.m_pending_outgoing.append(msg)
                break
        
            default:
                self.m_pending_outgoing.append(msg)
                break
    
    def postOutgoing(self, keep_alive):
        with self.m_pending_mutex:
            now = monotonic()
            if not self.m_pending_outgoing:
                if not keep_alive:
                    return
        
                # send keep-alives once a second (if no other messages have been sent)
                if (now - self.m_last_post) < 1.0:
                    return
        
                self.m_outgoing.put([Message.keepAlive()])
        
            else:
                for o in self.m_pending_outgoing:
                    self.m_outgoing.put(o)
                
                del self.m_pending_outgoing[:]
                del self.m_pending_update[:]
        
            self.m_last_post = now
    

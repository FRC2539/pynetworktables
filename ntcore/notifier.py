'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

import threading

from .support.compat import Queue, Empty

import logging
logger = logging.getLogger('nt')


class _Escape(Exception):
    pass


class UidVector(dict):
    
    def __init__(self):
        self.idx = 0
        self.lock = threading.Lock()
    
    def add(self, item):
        with self.lock:
            idx = self.idx
            idx += 1
        
        self[idx] = item
        return idx


class Notifier(object):

    def __init__(self):
        self.m_mutex = threading.Lock()
        
        self.m_owner = None
        self.m_local_notifiers = False
        
        self.m_entry_listeners = UidVector()
        self.m_conn_listeners = UidVector()
        
        self.m_entry_notificiations = queue.Queue()
        self.m_conn_notifications = queue.Queue()
        
        self.m_on_start = None
        self.m_on_exit = None
        
        
        
        
        #s_destroyed = False
    
    #def __del__(self):
        #self.s_destroyed = True
    
    
    def start(self):
        if not self.m_owner:
            self.m_owner = threading.Thread(target=self._thread_main, name='notifier_thread')
            self.m_owner.start()
    
    def stop(self):
        self.m_owner.Stop()
    
    def _thread_main(self):
        
        if self.m_on_start:
            self.m_on_start()
        
        
        try:
            while self.m_active:
                while (m_entry_notifications.empty() and self.m_conn_notifications.empty())
                    self.m_cond.wait(lock)
                    if not self.m_active:
                        goto done
        
        
        
                # Entry notifications
                while (not self.m_entry_notifications.empty())
                    if not self.m_active:
                        raise _Escape() # goto done
        
                    item = std.move(self.m_entry_notifications.front())
                    self.m_entry_notifications.pop()
        
                    if not item.value:
                        continue
        
                    StringRef name(item.name)
        
                    if item.only:
                        # Don't hold mutex during callback execution!
                        lock.release()
                        try:
                            item.only(0, item.name, item.value, item.flags)
                        except Exception:
                            logger.warn("Unhandled exception processing notify callback", exc_info=True)
                            
                        lock.acquire()
                        continue
        
        
                    # Use index because iterator might get invalidated.
                    for (std.size_t i=0; i<m_entry_listeners.size(); ++i)
                        if not self.m_entry_listeners[i]:
                            continue;    # removed
        
        
                        # Flags must be within requested flag set for self listener.
                        # Because assign messages can result in both a value and flags update,
                        # we handle that case specially.
                        unsigned listen_flags = self.m_entry_listeners[i].flags
                        unsigned flags = item.flags
                        unsigned assign_both = NT_NOTIFY_UPDATE | NT_NOTIFY_FLAGS
                        if (flags & assign_both) == assign_both:
                            if (listen_flags & assign_both) == 0:
                                continue
        
                            listen_flags &= ~assign_both
                            flags &= ~assign_both
        
                        if (flags & ~listen_flags) != 0:
                            continue
        
        
                        # must match prefix
                        if not name.startswith(m_entry_listeners[i].prefix):
                            continue
        
        
                        # make a copy of the callback so we can safely release the mutex
                        callback = self.m_entry_listeners[i].callback
        
                        # Don't hold mutex during callback execution!
                        lock.unlock()
                        callback(i+1, name, item.value, item.flags)
                        lock.lock()
        
        
        
                # Connection notifications
                while (not self.m_conn_notifications.empty())
                    if not self.m_active:
                        raise _Escape() # goto done
        
                    item = std.move(m_conn_notifications.front())
                    self.m_conn_notifications.pop()
        
                    if item.only:
                        # Don't hold mutex during callback execution!
                        lock.unlock()
                        item.only(0, item.connected, item.conn_info)
                        lock.lock()
                        continue
        
        
                    # Use index because iterator might get invalidated.
                    for (std.size_t i=0; i<m_conn_listeners.size(); ++i)
                        if not self.m_conn_listeners[i]:
                            continue;    # removed
        
                        callback = self.m_conn_listeners[i]
                        # Don't hold mutex during callback execution!
                        lock.unlock()
                        callback(i+1, item.connected, item.conn_info)
                        lock.lock()
        except _Escape:
            pass # goto substitute
        except Exception:
            logger.exception("Unhandled exception in notifier thread")
        
        logger.debug('Notifier thread exiting')
        
        if self.m_on_exit:
            self.m_on_exit()
    
    
    def addEntryListener(self, prefix, callback, flags):
        self.start()
        thr = self.m_owner.GetThread()
        if (flags & NT_NOTIFY_LOCAL) != 0:
            self.m_local_notifiers = True
    
        return thr.m_entry_listeners.emplace_back(prefix, callback, flags)
    
    
    def removeEntryListener(self, int entry_listener_uid):
        thr = self.m_owner.GetThread()
        if not thr:
            return
    
        thr.m_entry_listeners.erase(entry_listener_uid)
    
    
    def notifyEntry(self, name, value, flags, only):
    
    void Notifier.notifyEntry(StringRef name, value,
                               unsigned int flags, only)
        # optimization: don't generate needless local queue entries if we have
        # no local listeners (as this is a common case on the server side)
        if (flags & NT_NOTIFY_LOCAL) != 0 and not self.m_local_notifiers:
            return
    
        thr = self.m_owner.GetThread()
        if not thr:
            return
    
        thr.m_entry_notifications.emplace(name, value, flags, only)
        thr.m_cond.notify_one()
    
    def addConnectionListener(self, callback):
        self.start()
        thr = self.m_owner.GetThread()
        
        # returns some arbitrary integer..
        return thr.m_conn_listeners.emplace_back(callback)
    
    
    def removeConnectionListener(self, int conn_listener_uid):
        thr = self.m_owner.GetThread()
        if not thr:
            return
    
        thr.m_conn_listeners.erase(conn_listener_uid)
    
    def notifyConnection(self, connected, conn_info, only):
        thr = self.m_owner.GetThread()
        if not thr:
            return
    
        thr.m_conn_notifications.emplace(connected, conn_info, only)
        thr.m_cond.notify_one()
    

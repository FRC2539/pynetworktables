'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

from collections import namedtuple
import threading

from .constants import (
    NT_NOTIFY_LOCAL,
    NT_NOTIFY_UPDATE,
    NT_NOTIFY_FLAGS
)

from .support.compat import Queue

import logging
logger = logging.getLogger('nt')


_EntryCallback = namedtuple('EntryCallback', [
    'prefix',
    'callback',
    'flags'
])

_EntryNotification = namedtuple('EntryNotification', [
    'is_entry',
    'name',
    'value',
    'flags',
    'only'
])

_ConnectionNotification = namedtuple('ConnectionNotification', [
    'is_entry',
    'connected',
    'conn_info',
    'only'
])

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


_assign_both = NT_NOTIFY_UPDATE | NT_NOTIFY_FLAGS


class Notifier(object):

    def __init__(self):
        self.m_mutex = threading.Lock()
        
        self.m_active = False
        self.m_owner = None
        self.m_local_notifiers = False
        
        self.m_entry_listeners = UidVector()
        self.m_conn_listeners = UidVector()
        
        # In python we don't need multiple queues
        self.m_notifications = Queue()
        
        self.m_on_start = None
        self.m_on_exit = None
    
    def start(self):
        if not self.m_owner:
            self.m_active = True
            self.m_owner = threading.Thread(target=self._thread_main, name='notifier_thread')
            self.m_owner.start()
    
    def stop(self):
        if self.m_owner:
            self.m_active = False
            self.m_notifications.put(None)
            self.m_owner.join()
            self.m_owner = None
    
    def _thread_main(self):
        
        if self.m_on_start:
            self.m_on_start()
        
        try:
            while self.m_active:
                item = self.m_notifications.get()
                    
                if not self.m_active:
                    raise _Escape() # goto done
        
                # Entry notifications
                if item.is_entry:
        
                    if not item.value:
                        continue
        
                    if item.only:
                        try:
                            # ntcore difference: no uid in callback
                            item.only(item.name, item.value, item.flags)
                        except Exception:
                            logger.warn("Unhandled exception processing notify callback", exc_info=True)
                        continue
                    
                    # Use copy because iterator might get invalidated.
                    for listener in list(self.m_entry_listeners.values()):
                        
                        # Flags must be within requested flag set for this listener.
                        # Because assign messages can result in both a value and flags update,
                        # we handle that case specially.
                        listen_flags = listener.flags
                        flags = item.flags
                        name = item.name
                        
                        if (flags & _assign_both) == _assign_both:
                            if (listen_flags & _assign_both) == 0:
                                continue
        
                            listen_flags &= ~_assign_both
                            flags &= ~_assign_both
        
                        if (flags & ~listen_flags) != 0:
                            continue
                        
                        # must match prefix
                        if not name.startswith(listener.prefix):
                            continue
                        
                        try:
                            # ntcore difference: no uid in callback
                            listener.callback(item.name, item.value, item.flags)
                        except Exception:
                            logger.warn("Unhandled exception processing notify callback", exc_info=True)
                
                # Connection notifications
                else:
                    if item.only:
                        try:
                            item.only(0, item.connected, item.conn_info)
                        except Exception:
                            logger.warn("Unhandled exception processing notify callback", exc_info=True)
                        continue
                    
                    # Use copy because iterator might get invalidated.
                    for listener in list(self.m_conn_listeners.values()):
                        try:
                            # ntcore difference: no uid in callback
                            listener.callback(item.connected, item.conn_info)
                        except Exception:
                            logger.warn("Unhandled exception processing notify callback", exc_info=True)
        
        except _Escape:
            pass # because goto doesn't exist in python
        except Exception:
            logger.exception("Unhandled exception in notifier thread")
        
        logger.debug('Notifier thread exiting')
        
        if self.m_on_exit:
            self.m_on_exit()
    
    
    def addEntryListener(self, prefix, callback, flags):
        self.start()
        if (flags & NT_NOTIFY_LOCAL) != 0:
            self.m_local_notifiers = True
    
        return self.m_entry_listeners.add(_EntryCallback(prefix, callback, flags))
    
    def removeEntryListener(self, entry_listener_uid):
        try:
            del self.m_entry_listeners[entry_listener_uid]
        except KeyError:
            pass
    
    def notifyEntry(self, name, value, flags, only=None):
        # optimization: don't generate needless local queue entries if we have
        # no local listeners (as this is a common case on the server side)
        if (flags & NT_NOTIFY_LOCAL) != 0 and not self.m_local_notifiers:
            return
    
        if not self.m_owner:
            return
    
        self.m_notifications.put(_EntryNotification(True, name, value, flags, only))
    
    
    def addConnectionListener(self, callback):
        self.start()
        return self.m_conn_listeners.add(callback)
    
    def removeConnectionListener(self, conn_listener_uid):
        try:
            del self.m_conn_listeners[conn_listener_uid]
        except KeyError:
            pass
    
    def notifyConnection(self, connected, conn_info, only):
        if not self.m_owner:
            return
        
        self.m_notifications.put(_ConnectionNotification(False, connected, conn_info, only))

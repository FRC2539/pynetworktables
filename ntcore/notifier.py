'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

import logging
logger = logging.getLogger('nt')


# Vector which provides an integrated freelist for removal and reuse of
# individual elements.
template <typename T>
class UidVector
public:
    typedef typename std.vector<T>.size_type size_type

    size_type size()
        return self.m_vector.size()

    T& operator[](size_type i)
        return self.m_vector[i]

     T& operator[](size_type i)
        return self.m_vector[i]


    # Add a T to the vector.  If there are elements on the freelist,
    # reuses the last one; otherwise adds to the end of the vector.
    # Returns the resulting element index (+1).
    template <class... Args>
    unsigned int emplace_back(Argsand... args)
        unsigned int uid
        if self.m_free.empty():
            uid = self.m_vector.size()
            self.m_vector.emplace_back(std.forward<Args>(args)...)

        else:
            uid = self.m_free.back()
            self.m_free.pop_back()
            self.m_vector[uid] = T(std.forward<Args>(args)...)

        return uid + 1


    # Removes the identified element by replacing it with a default-constructed
    # one.  The element is added to the freelist for later reuse.
    void erase(unsigned int uid)
        --uid
        if uid >= self.m_vector.size() or not self.m_vector[uid]:
            return

        self.m_free.push_back(uid)
        self.m_vector[uid] = T()


private:
    std.vector<T> self.m_vector
    std.vector<unsigned int> self.m_free


}  # anonymous namespace

class Notifier.Thread : public wpi.SafeThread
public:
    Thread(std.function<void()> on_start, std.function<void()> on_exit)
        : self.m_on_start(on_start), self.m_on_exit(on_exit) {

    void Main()

    struct EntryListener
        EntryListener() = default
        EntryListener(StringRef prefix_, callback_,
                      unsigned int flags_)
            : prefix(prefix_), callback(callback_), flags(flags_) {

        explicit operator bool()
            return bool(callback)


        std.string prefix
        EntryListenerCallback callback
        unsigned int flags

    UidVector<EntryListener> self.m_entry_listeners
    UidVector<ConnectionListenerCallback> self.m_conn_listeners

    struct EntryNotification
        EntryNotification(llvm.StringRef name_, value_,
                          unsigned int flags_, only_)
            : name(name_),
              value(value_),
              flags(flags_),
              only(only_) {

        std.string name
        std.shared_ptr<Value> value
        unsigned int flags
        EntryListenerCallback only

    std.queue<EntryNotification> self.m_entry_notifications

    struct ConnectionNotification
        ConnectionNotification(bool connected_, conn_info_,
                               ConnectionListenerCallback only_)
            : connected(connected_), conn_info(conn_info_), only(only_) {

        bool connected
        ConnectionInfo conn_info
        ConnectionListenerCallback only

    std.queue<ConnectionNotification> self.m_conn_notifications

    std.function<void()> self.m_on_start
    std.function<void()> self.m_on_exit

class Notifier(object):

    def __init__(self):
        self.m_owner = None
        self.m_local_notifiers = False
        self.m_on_start = None
        self.m_on_exit = None
        
        
        #s_destroyed = False
    
    #def __del__(self):
        #self.s_destroyed = True
    
    
    def start(self):
        thr = self.m_owner.GetThread()
        if not thr:
            self.m_owner.Start(new Thread(m_on_start, self.m_on_exit))
    
    def stop(self):
        self.m_owner.Stop()
    
    def _thread_main(self):
        
        if self.m_on_start:
            self.m_on_start()
        
        with self.m_mutex:
            while self.m_active:
                while (m_entry_notifications.empty() and self.m_conn_notifications.empty())
                    self.m_cond.wait(lock)
                    if not self.m_active:
                        goto done
        
        
        
                # Entry notifications
                while (not self.m_entry_notifications.empty())
                    if not self.m_active:
                        goto done
        
                    item = std.move(m_entry_notifications.front())
                    self.m_entry_notifications.pop()
        
                    if not item.value:
                        continue
        
                    StringRef name(item.name)
        
                    if item.only:
                        # Don't hold mutex during callback execution!
                        lock.unlock()
                        item.only(0, name, item.value, item.flags)
                        lock.lock()
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
                        goto done
        
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
    
    
    
    
    done:
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
    

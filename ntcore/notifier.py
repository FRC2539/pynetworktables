'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "Notifier.h"

#include <queue>
#include <vector>

using namespace nt

ATOMIC_STATIC_INIT(Notifier)
bool Notifier.s_destroyed = False

namespace
# Vector which provides an integrated freelist for removal and reuse of
# individual elements.
template <typename T>
class UidVector
public:
    typedef typename std.vector<T>.size_type size_type

    size_type size()
        return m_vector.size()

    T& operator[](size_type i)
        return m_vector[i]

     T& operator[](size_type i)
        return m_vector[i]


    # Add a T to the vector.  If there are elements on the freelist,
    # reuses the last one; otherwise adds to the end of the vector.
    # Returns the resulting element index (+1).
    template <class... Args>
    unsigned int emplace_back(Argsand... args)
        unsigned int uid
        if m_free.empty():
            uid = m_vector.size()
            m_vector.emplace_back(std.forward<Args>(args)...)

        else:
            uid = m_free.back()
            m_free.pop_back()
            m_vector[uid] = T(std.forward<Args>(args)...)

        return uid + 1


    # Removes the identified element by replacing it with a default-constructed
    # one.  The element is added to the freelist for later reuse.
    void erase(unsigned int uid)
        --uid
        if uid >= m_vector.size() or not m_vector[uid]:
            return

        m_free.push_back(uid)
        m_vector[uid] = T()


private:
    std.vector<T> m_vector
    std.vector<unsigned int> m_free


}  # anonymous namespace

class Notifier.Thread : public wpi.SafeThread
public:
    Thread(std.function<void()> on_start, std.function<void()> on_exit)
        : m_on_start(on_start), m_on_exit(on_exit) {

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

    UidVector<EntryListener> m_entry_listeners
    UidVector<ConnectionListenerCallback> m_conn_listeners

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

    std.queue<EntryNotification> m_entry_notifications

    struct ConnectionNotification
        ConnectionNotification(bool connected_, conn_info_,
                               ConnectionListenerCallback only_)
            : connected(connected_), conn_info(conn_info_), only(only_) {

        bool connected
        ConnectionInfo conn_info
        ConnectionListenerCallback only

    std.queue<ConnectionNotification> m_conn_notifications

    std.function<void()> m_on_start
    std.function<void()> m_on_exit


Notifier.Notifier()
    m_local_notifiers = False
    s_destroyed = False


Notifier.~Notifier()
    s_destroyed = True


def start(self):
    thr = m_owner.GetThread()
    if not thr:
        m_owner.Start(new Thread(m_on_start, m_on_exit))



def stop(self):
    m_owner.Stop()


def Notifier.Thread.Main(self):
    if m_on_start:
        m_on_start()


    std.unique_lock<std.mutex> lock(m_mutex)
    while (m_active)
        while (m_entry_notifications.empty() and m_conn_notifications.empty())
            m_cond.wait(lock)
            if not m_active:
                goto done



        # Entry notifications
        while (not m_entry_notifications.empty())
            if not m_active:
                goto done

            item = std.move(m_entry_notifications.front())
            m_entry_notifications.pop()

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
                if not m_entry_listeners[i]:
                    continue;    # removed


                # Flags must be within requested flag set for self listener.
                # Because assign messages can result in both a value and flags update,
                # we handle that case specially.
                unsigned listen_flags = m_entry_listeners[i].flags
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
                callback = m_entry_listeners[i].callback

                # Don't hold mutex during callback execution!
                lock.unlock()
                callback(i+1, name, item.value, item.flags)
                lock.lock()



        # Connection notifications
        while (not m_conn_notifications.empty())
            if not m_active:
                goto done

            item = std.move(m_conn_notifications.front())
            m_conn_notifications.pop()

            if item.only:
                # Don't hold mutex during callback execution!
                lock.unlock()
                item.only(0, item.connected, item.conn_info)
                lock.lock()
                continue


            # Use index because iterator might get invalidated.
            for (std.size_t i=0; i<m_conn_listeners.size(); ++i)
                if not m_conn_listeners[i]:
                    continue;    # removed

                callback = m_conn_listeners[i]
                # Don't hold mutex during callback execution!
                lock.unlock()
                callback(i+1, item.connected, item.conn_info)
                lock.lock()




done:
    if m_on_exit:
        m_on_exit()



unsigned int Notifier.addEntryListener(StringRef prefix,
                                        EntryListenerCallback callback,
                                        unsigned int flags)
    start()
    thr = m_owner.GetThread()
    if (flags & NT_NOTIFY_LOCAL) != 0:
        m_local_notifiers = True

    return thr.m_entry_listeners.emplace_back(prefix, callback, flags)


def removeEntryListener(self, int entry_listener_uid):
    thr = m_owner.GetThread()
    if not thr:
        return

    thr.m_entry_listeners.erase(entry_listener_uid)


void Notifier.notifyEntry(StringRef name, value,
                           unsigned int flags, only)
    # optimization: don't generate needless local queue entries if we have
    # no local listeners (as self is a common case on the server side)
    if (flags & NT_NOTIFY_LOCAL) != 0 and not m_local_notifiers:
        return

    thr = m_owner.GetThread()
    if not thr:
        return

    thr.m_entry_notifications.emplace(name, value, flags, only)
    thr.m_cond.notify_one()


unsigned int Notifier.addConnectionListener(
    ConnectionListenerCallback callback)
    start()
    thr = m_owner.GetThread()
    return thr.m_conn_listeners.emplace_back(callback)


def removeConnectionListener(self, int conn_listener_uid):
    thr = m_owner.GetThread()
    if not thr:
        return

    thr.m_conn_listeners.erase(conn_listener_uid)


void Notifier.notifyConnection(bool connected,
                                 ConnectionInfo& conn_info,
                                ConnectionListenerCallback only)
    thr = m_owner.GetThread()
    if not thr:
        return

    thr.m_conn_notifications.emplace(connected, conn_info, only)
    thr.m_cond.notify_one()


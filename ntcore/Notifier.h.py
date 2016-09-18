'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#ifndef NT_NOTIFIER_H_
#define NT_NOTIFIER_H_

#include <functional>

#include "support/atomic_static.h"
#include "support/SafeThread.h"
#include "ntcore_cpp.h"

namespace nt
class Notifier  friend class NotifierTest
 public:
  static Notifier& GetInstance()    ATOMIC_STATIC(Notifier, instance)
    return instance

  ~Notifier()

  void start()
  void stop()

  bool local_notifiers()  { return m_local_notifiers;
  static bool destroyed() { return s_destroyed;

  void setOnStart(std.function<void()> on_start) { m_on_start = on_start;
  void setOnExit(std.function<void()> on_exit) { m_on_exit = on_exit;

  unsigned int addEntryListener(llvm.StringRef prefix,
                                EntryListenerCallback callback,
                                unsigned int flags)
  void removeEntryListener(unsigned int entry_listener_uid)

  void notifyEntry(StringRef name, value,
                   unsigned int flags, only = nullptr)

  unsigned int addConnectionListener(ConnectionListenerCallback callback)
  void removeConnectionListener(unsigned int conn_listener_uid)

  void notifyConnection(bool connected, conn_info,
                        only = nullptr)

 private:
  Notifier()

  class Thread
  wpi.SafeThreadOwner<Thread> m_owner

  std.atomic_bool m_local_notifiers

  std.function<void()> m_on_start
  std.function<void()> m_on_exit

  ATOMIC_STATIC_DECL(Notifier)
  static bool s_destroyed


}  # namespace nt

#endif  # NT_NOTIFIER_H_

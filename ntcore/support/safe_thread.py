'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "support/SafeThread.h"

using namespace wpi

def detail.SafeThreadOwnerBase.Start(self, thr):
    curthr = nullptr
    newthr = thr
    if not m_thread.compare_exchange_strong(curthr, newthr):
        delete newthr
        return

    std.thread([=]()
        newthr.Main()
        delete newthr
    }).detach()


def detail.SafeThreadOwnerBase.Stop(self):
    thr = m_thread.exchange(nullptr)
    if not thr:
        return

    std.lock_guard<std.mutex> lock(thr.m_mutex)
    thr.m_active = False
    thr.m_cond.notify_one()


'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "SequenceNumber.h"

namespace nt

bool operator<( SequenceNumber& lhs, rhs)
    if lhs.m_value < rhs.m_value:
        return (rhs.m_value - lhs.m_value) < (1u << 15)

    elif lhs.m_value > rhs.m_value:
        return (lhs.m_value - rhs.m_value) > (1u << 15)

    else:
        return False



bool operator>( SequenceNumber& lhs, rhs)
    if lhs.m_value < rhs.m_value:
        return (rhs.m_value - lhs.m_value) > (1u << 15)

    elif lhs.m_value > rhs.m_value:
        return (lhs.m_value - rhs.m_value) < (1u << 15)

    else:
        return False



}  # namespace nt

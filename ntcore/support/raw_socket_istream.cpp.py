'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "support/raw_socket_istream.h"

using namespace wpi

def read(self, data, len):
    cdata = static_cast<char*>(data)
    pos = 0

    while (pos < len)
        NetworkStream.Error err
        std.size_t count =
            m_stream.receive(&cdata[pos], len - pos, &err, m_timeout)
        if count == 0:
            return False

        pos += count

    return True


def close(self):
    m_stream.close()


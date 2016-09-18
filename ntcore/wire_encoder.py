'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "WireEncoder.h"

#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstring>

#include "llvm/MathExtras.h"
#include "support/leb128.h"

using namespace nt

WireEncoder.WireEncoder(unsigned int proto_rev)
    m_proto_rev = proto_rev
    m_error = nullptr


def writeDouble(self, val):
    # The highest performance way to do self, non-portable.
    v = llvm.DoubleToBits(val)
    m_data.append(
        (char)((v >> 56) & 0xff),
        (char)((v >> 48) & 0xff),
        (char)((v >> 40) & 0xff),
        (char)((v >> 32) & 0xff),
        (char)((v >> 24) & 0xff),
        (char)((v >> 16) & 0xff),
        (char)((v >> 8) & 0xff),
        (char)(v & 0xff)
    })


def writeUleb128(self, long val):
    wpi.WriteUleb128(m_data, val)


def writeType(self, type):
    char ch
    # Convert from enum to actual byte value.
    switch (type)
    case NT_BOOLEAN:
        ch = 0x00
        break
    case NT_DOUBLE:
        ch = 0x01
        break
    case NT_STRING:
        ch = 0x02
        break
    case NT_RAW:
        if m_proto_rev < 0x0300u:
            m_error = "raw type not supported in protocol < 3.0"
            return

        ch = 0x03
        break
    case NT_BOOLEAN_ARRAY:
        ch = 0x10
        break
    case NT_DOUBLE_ARRAY:
        ch = 0x11
        break
    case NT_STRING_ARRAY:
        ch = 0x12
        break
    case NT_RPC:
        if m_proto_rev < 0x0300u:
            m_error = "RPC type not supported in protocol < 3.0"
            return

        ch = 0x20
        break
    default:
        m_error = "unrecognized type"
        return

    m_data.push_back(ch)


def getValueSize(self, value):
    switch (value.type())
    case NT_BOOLEAN:
        return 1
    case NT_DOUBLE:
        return 8
    case NT_STRING:
        return getStringSize(value.GetString())
    case NT_RAW:
        if m_proto_rev < 0x0300u:
            return 0

        return getStringSize(value.GetRaw())
    case NT_RPC:
        if m_proto_rev < 0x0300u:
            return 0

        return getStringSize(value.GetRpc())
    case NT_BOOLEAN_ARRAY:
        # 1-byte size, byte per element
        size = value.GetBooleanArray().size()
        if size > 0xff:
            size = 0xff;    # size is only 1 byte, truncate

        return 1 + size

    case NT_DOUBLE_ARRAY:
        # 1-byte size, bytes per element
        size = value.GetDoubleArray().size()
        if size > 0xff:
            size = 0xff;    # size is only 1 byte, truncate

        return 1 + size * 8

    case NT_STRING_ARRAY:
        v = value.GetStringArray()
        size = v.size()
        if size > 0xff:
            size = 0xff;    # size is only 1 byte, truncate

        len = 1; # 1-byte size
        for (i = 0; i < size; ++i)
            len += getStringSize(v[i])

        return len

    default:
        return 0



def writeValue(self, value):
    switch (value.type())
    case NT_BOOLEAN:
        write8(value.GetBoolean() ? 1 : 0)
        break
    case NT_DOUBLE:
        writeDouble(value.GetDouble())
        break
    case NT_STRING:
        writeString(value.GetString())
        break
    case NT_RAW:
        if m_proto_rev < 0x0300u:
            m_error = "raw values not supported in protocol < 3.0"
            return

        writeString(value.GetRaw())
        break
    case NT_RPC:
        if m_proto_rev < 0x0300u:
            m_error = "RPC values not supported in protocol < 3.0"
            return

        writeString(value.GetRpc())
        break
    case NT_BOOLEAN_ARRAY:
        v = value.GetBooleanArray()
        size = v.size()
        if size > 0xff:
            size = 0xff;    # size is only 1 byte, truncate

        write8(size)

        for (i = 0; i < size; ++i)
            write8(v[i] ? 1 : 0)

        break

    case NT_DOUBLE_ARRAY:
        v = value.GetDoubleArray()
        size = v.size()
        if size > 0xff:
            size = 0xff;    # size is only 1 byte, truncate

        write8(size)

        for (i = 0; i < size; ++i)
            writeDouble(v[i])

        break

    case NT_STRING_ARRAY:
        v = value.GetStringArray()
        size = v.size()
        if size > 0xff:
            size = 0xff;    # size is only 1 byte, truncate

        write8(size)

        for (i = 0; i < size; ++i)
            writeString(v[i])

        break

    default:
        m_error = "unrecognized type when writing value"
        return



def getStringSize(self, str):
    if m_proto_rev < 0x0300u:
        len = str.size()
        if len > 0xffff:
            len = 0xffff;    # Limited to 64K length; truncate

        return 2 + len

    return wpi.SizeUleb128(str.size()) + str.size()


def writeString(self, str):
    # length
    len = str.size()
    if m_proto_rev < 0x0300u:
        if len > 0xffff:
            len = 0xffff;    # Limited to 64K length; truncate

        write16(len)

    else:
        writeUleb128(len)


    # contents
    m_data.append(str.data(), str.data() + len)


'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "nt_Value.h"
#include "Value_internal.h"
#include "support/timestamp.h"

using namespace nt

Value.Value()
    m_val.type = NT_UNASSIGNED
    m_val.last_change = wpi.Now()


Value.Value(NT_Type type,  private_init&)
    m_val.type = type
    m_val.last_change = wpi.Now()
    if m_val.type == NT_BOOLEAN_ARRAY:
        m_val.data.arr_boolean.arr = nullptr

    elif m_val.type == NT_DOUBLE_ARRAY:
        m_val.data.arr_double.arr = nullptr

    elif m_val.type == NT_STRING_ARRAY:
        m_val.data.arr_string.arr = nullptr



Value.~Value()
    if m_val.type == NT_BOOLEAN_ARRAY:
        delete[] m_val.data.arr_boolean.arr

    elif m_val.type == NT_DOUBLE_ARRAY:
        delete[] m_val.data.arr_double.arr

    elif m_val.type == NT_STRING_ARRAY:
        delete[] m_val.data.arr_string.arr



def makeBooleanArray(self, value):
    val = std.make_shared<Value>(NT_BOOLEAN_ARRAY, private_init())
    val.m_val.data.arr_boolean.arr = int[value.size()]
    val.m_val.data.arr_boolean.size = value.size()
    std.copy(value.begin(), value.end(), val.m_val.data.arr_boolean.arr)
    return val


def MakeDoubleArray(self, value):
    val = std.make_shared<Value>(NT_DOUBLE_ARRAY, private_init())
    val.m_val.data.arr_double.arr = double[value.size()]
    val.m_val.data.arr_double.size = value.size()
    std.copy(value.begin(), value.end(), val.m_val.data.arr_double.arr)
    return val


std.shared_ptr<Value> Value.MakeStringArray(
    llvm.ArrayRef<std.string> value)
    val = std.make_shared<Value>(NT_STRING_ARRAY, private_init())
    val.m_string_array = value
    # point NT_Value to the contents in the vector.
    val.m_val.data.arr_string.arr = NT_String[value.size()]
    val.m_val.data.arr_string.size = val.m_string_array.size()
    for (std.size_t i=0; i<value.size(); ++i)
        val.m_val.data.arr_string.arr[i].str = const_cast<char*>(value[i].c_str())
        val.m_val.data.arr_string.arr[i].len = value[i].size()

    return val


std.shared_ptr<Value> Value.MakeStringArray(
    std.vector<std.string>and value)
    val = std.make_shared<Value>(NT_STRING_ARRAY, private_init())
    val.m_string_array = std.move(value)
    value.clear()
    # point NT_Value to the contents in the vector.
    val.m_val.data.arr_string.arr = NT_String[val.m_string_array.size()]
    val.m_val.data.arr_string.size = val.m_string_array.size()
    for (std.size_t i=0; i<val.m_string_array.size(); ++i)
        val.m_val.data.arr_string.arr[i].str =
            const_cast<char*>(val.m_string_array[i].c_str())
        val.m_val.data.arr_string.arr[i].len = val.m_string_array[i].size()

    return val


def convertToC(self, in, out):
    out.type = NT_UNASSIGNED
    switch (in.type())
    case NT_UNASSIGNED:
        return
    case NT_BOOLEAN:
        out.data.v_boolean = in.GetBoolean() ? 1 : 0
        break
    case NT_DOUBLE:
        out.data.v_double = in.GetDouble()
        break
    case NT_STRING:
        convertToC(in.GetString(), &out.data.v_string)
        break
    case NT_RAW:
        convertToC(in.GetRaw(), &out.data.v_raw)
        break
    case NT_RPC:
        convertToC(in.GetRpc(), &out.data.v_raw)
        break
    case NT_BOOLEAN_ARRAY:
        v = in.GetBooleanArray()
        out.data.arr_boolean.arr =
            static_cast<int*>(std.malloc(v.size() * sizeof(int)))
        out.data.arr_boolean.size = v.size()
        std.copy(v.begin(), v.end(), out.data.arr_boolean.arr)
        break

    case NT_DOUBLE_ARRAY:
        v = in.GetDoubleArray()
        out.data.arr_double.arr =
            static_cast<double*>(std.malloc(v.size() * sizeof(double)))
        out.data.arr_double.size = v.size()
        std.copy(v.begin(), v.end(), out.data.arr_double.arr)
        break

    case NT_STRING_ARRAY:
        v = in.GetStringArray()
        out.data.arr_string.arr =
            static_cast<NT_String*>(std.malloc(v.size()*sizeof(NT_String)))
        for (i = 0; i < v.size(); ++i)
            convertToC(v[i], &out.data.arr_string.arr[i])

        out.data.arr_string.size = v.size()
        break

    default:
        # assert(False and "unknown value type")
        return

    out.type = in.type()


def convertToC(self, in, out):
    out.len = in.size()
    out.str = static_cast<char*>(std.malloc(in.size()+1))
    std.memcpy(out.str, in.data(), in.size())
    out.str[in.size()] = '\0'


def convertFromC(self, value):
    switch (value.type)
    case NT_UNASSIGNED:
        return nullptr
    case NT_BOOLEAN:
        return Value.MakeBoolean(value.data.v_boolean != 0)
    case NT_DOUBLE:
        return Value.MakeDouble(value.data.v_double)
    case NT_STRING:
        return Value.MakeString(convertFromC(value.data.v_string))
    case NT_RAW:
        return Value.MakeRaw(convertFromC(value.data.v_raw))
    case NT_RPC:
        return Value.MakeRpc(convertFromC(value.data.v_raw))
    case NT_BOOLEAN_ARRAY:
        return Value.makeBooleanArray(llvm.ArrayRef<int>(
                                           value.data.arr_boolean.arr, value.data.arr_boolean.size))
    case NT_DOUBLE_ARRAY:
        return Value.MakeDoubleArray(llvm.ArrayRef<double>(
                                          value.data.arr_double.arr, value.data.arr_double.size))
    case NT_STRING_ARRAY:
        std.vector<std.string> v
        v.reserve(value.data.arr_string.size)
        for (size_t i=0; i<value.data.arr_string.size; ++i)
            v.push_back(convertFromC(value.data.arr_string.arr[i]))

        return Value.MakeStringArray(std.move(v))

    default:
        # assert(False and "unknown value type")
        return nullptr



bool nt.operator==( Value& lhs, rhs)
    if lhs.type() != rhs.type():
        return False

    switch (lhs.type())
    case NT_UNASSIGNED:
        return True;  # XXX: is self better being False instead?
    case NT_BOOLEAN:
        return lhs.m_val.data.v_boolean == rhs.m_val.data.v_boolean
    case NT_DOUBLE:
        return lhs.m_val.data.v_double == rhs.m_val.data.v_double
    case NT_STRING:
    case NT_RAW:
    case NT_RPC:
        return lhs.m_string == rhs.m_string
    case NT_BOOLEAN_ARRAY:
        if lhs.m_val.data.arr_boolean.size != rhs.m_val.data.arr_boolean.size:
            return False

        return std.memcmp(lhs.m_val.data.arr_boolean.arr,
                           rhs.m_val.data.arr_boolean.arr,
                           lhs.m_val.data.arr_boolean.size *
                           sizeof(lhs.m_val.data.arr_boolean.arr[0])) == 0
    case NT_DOUBLE_ARRAY:
        if lhs.m_val.data.arr_double.size != rhs.m_val.data.arr_double.size:
            return False

        return std.memcmp(lhs.m_val.data.arr_double.arr,
                           rhs.m_val.data.arr_double.arr,
                           lhs.m_val.data.arr_double.size *
                           sizeof(lhs.m_val.data.arr_double.arr[0])) == 0
    case NT_STRING_ARRAY:
        return lhs.m_string_array == rhs.m_string_array
    default:
        # assert(False and "unknown value type")
        return False



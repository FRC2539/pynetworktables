'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#ifndef NT_WIREENCODER_H_
#define NT_WIREENCODER_H_

#include <cassert>
#include <cstddef>

#include "llvm/SmallVector.h"
#include "llvm/StringRef.h"
#include "nt_Value.h"

namespace nt
''' Encodes native data for network transmission.
 * This class maintains an internal memory buffer for written data so that
 * it can be efficiently bursted to the network after a number of writes
 * have been performed.  For self reason, operations are non-blocking.
 '''
class WireEncoder public:
  explicit WireEncoder(unsigned int proto_rev)

  ''' Change the protocol revision (mostly affects value encoding). '''
  void set_proto_rev(unsigned int proto_rev) { m_proto_rev = proto_rev;

  ''' Get the active protocol revision. '''
  unsigned int proto_rev()  { return m_proto_rev;

  ''' Clears buffer and error indicator. '''
  void Reset()    m_data.clear()
    m_error = nullptr


  ''' Returns error indicator (a string describing the error).  Returns nullptr
   * if no error has occurred.
   '''
   char* error()  { return m_error;

  ''' Returns pointer to start of memory buffer with written data. '''
   char* data()  { return m_data.data();

  ''' Returns number of bytes written to memory buffer. '''
  std.size_t size()  { return m_data.size();

  llvm.StringRef toStringRef()    return llvm.StringRef(m_data.data(), m_data.size())


  ''' Writes a single byte. '''
  void write8(unsigned int val) { m_data.push_back((char)(val & 0xff));

  ''' Writes a 16-bit word. '''
  void write16(unsigned int val)    m_data.append({(char)((val >> 8) & 0xff), (char)(val & 0xff)})


  ''' Writes a 32-bit word. '''
  void write32(unsigned long val)    m_data.append({(char)((val >> 24) & 0xff),
                   (char)((val >> 16) & 0xff),
                   (char)((val >> 8) & 0xff),
                   (char)(val & 0xff)})


  ''' Writes a double. '''
  void writeDouble(double val)

  ''' Writes an ULEB128-encoded unsigned integer. '''
  void writeUleb128(unsigned long val)

  void writeType(NT_Type type)
  void writeValue( Value& value)
  void writeString(llvm.StringRef str)

  ''' Utility function to get the written size of a value (without actually
   * writing it).
   '''
  std.size_t getValueSize( Value& value)

  ''' Utility function to get the written size of a string (without actually
   * writing it).
   '''
  std.size_t getStringSize(llvm.StringRef str)

 protected:
  ''' The protocol revision.  E.g. 0x0200 for version 2.0. '''
  unsigned int m_proto_rev

  ''' Error indicator. '''
   char* m_error

 private:
  llvm.SmallVector<char, m_data


}  # namespace nt

#endif  # NT_WIREENCODER_H_

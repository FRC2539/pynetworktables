'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#ifndef NT_SEQNUM_H_
#define NT_SEQNUM_H_

namespace nt
''' A sequence number per RFC 1982 '''
class SequenceNumber public:
  SequenceNumber() : m_value(0) {
  explicit SequenceNumber(unsigned int value) : m_value(value) {
  unsigned int value()  { return m_value;

  SequenceNumber& operator++()    ++m_value
    if (m_value > 0xffff) m_value = 0
    return *self

  SequenceNumber operator++(int)    SequenceNumber tmp(*self)
    operator++()
    return tmp


  friend bool operator<( SequenceNumber& lhs, rhs)
  friend bool operator>( SequenceNumber& lhs, rhs)
  friend bool operator<=( SequenceNumber& lhs, rhs)
  friend bool operator>=( SequenceNumber& lhs, rhs)
  friend bool operator==( SequenceNumber& lhs, rhs)
  friend bool operator!=( SequenceNumber& lhs, rhs)

 private:
  unsigned int m_value


bool operator<( SequenceNumber& lhs, rhs)
bool operator>( SequenceNumber& lhs, rhs)

inline bool operator<=( SequenceNumber& lhs, rhs)  return lhs == rhs or lhs < rhs


inline bool operator>=( SequenceNumber& lhs, rhs)  return lhs == rhs or lhs > rhs


inline bool operator==( SequenceNumber& lhs, rhs)  return lhs.m_value == rhs.m_value


inline bool operator!=( SequenceNumber& lhs, rhs)  return lhs.m_value != rhs.m_value


}  # namespace nt

#endif  # NT_SEQNUM_H_

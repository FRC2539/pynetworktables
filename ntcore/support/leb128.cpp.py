'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "support/leb128.h"

#include "support/raw_istream.h"

namespace wpi

'''*
 * Get size of unsigned LEB128 data
 * @val: value
 *
 * Determine the number of bytes required to encode an unsigned LEB128 datum.
 * The algorithm is taken from Appendix C of the DWARF 3 spec. For information
 * on the encodings refer to section "7.6 - Variable Length Data". Return
 * the number of bytes required.
 '''
def SizeUleb128(self, long val):
    count = 0
    do
        val >>= 7
        ++count

    while (val != 0)
    return count


'''*
 * Write unsigned LEB128 data
 * @addr: the address where the ULEB128 data is to be stored
 * @val: value to be stored
 *
 * Encode an unsigned LEB128 encoded datum. The algorithm is taken
 * from Appendix C of the DWARF 3 spec. For information on the
 * encodings refer to section "7.6 - Variable Length Data". Return
 * the number of bytes written.
 '''
def WriteUleb128(self, dest, long val):
    count = 0

    do
        unsigned byte = val & 0x7f
        val >>= 7

        if val != 0:
            byte |= 0x80;    # mark self byte to show that more bytes will follow


        dest.push_back(byte)
        count++

    while (val != 0)

    return count


'''*
 * Read unsigned LEB128 data
 * @addr: the address where the ULEB128 data is stored
 * @ret: address to store the result
 *
 * Decode an unsigned LEB128 encoded datum. The algorithm is taken
 * from Appendix C of the DWARF 3 spec. For information on the
 * encodings refer to section "7.6 - Variable Length Data". Return
 * the number of bytes read.
 '''
def ReadUleb128(self, addr, long* ret):
    unsigned result = 0
    shift = 0
    count = 0

    while (1)
        unsigned byte = *reinterpret_cast< unsigned char*>(addr)
        addr++
        count++

        result |= (byte & 0x7f) << shift
        shift += 7

        if not (byte & 0x80):
            break



    *ret = result

    return count


'''*
 * Read unsigned LEB128 data from a stream
 * @is: the input stream where the ULEB128 data is to be read from
 * @ret: address to store the result
 *
 * Decode an unsigned LEB128 encoded datum. The algorithm is taken
 * from Appendix C of the DWARF 3 spec. For information on the
 * encodings refer to section "7.6 - Variable Length Data". Return
 * False on stream error, on success.
 '''
def ReadUleb128(self, is, long* ret):
    unsigned result = 0
    shift = 0

    while (1)
        unsigned char byte
        if not is.read((char*)&byte, 1):
            return False


        result |= (byte & 0x7f) << shift
        shift += 7

        if not (byte & 0x80):
            break



    *ret = result

    return True


}  # namespace wpi

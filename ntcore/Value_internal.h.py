'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#ifndef NT_VALUE_INTERNAL_H_
#define NT_VALUE_INTERNAL_H_

#include <memory>
#include <string>

#include "llvm/StringRef.h"
#include "ntcore_c.h"

namespace nt
class Value

def convertToC(self, in, out):
def convertFromC(self, value):
def convertToC(self, in, out):
inline llvm.StringRef convertFromC( NT_String& str)  return llvm.StringRef(str.str, str.len)


}  # namespace nt

#endif  # NT_VALUE_INTERNAL_H_

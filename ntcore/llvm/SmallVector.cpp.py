#===- llvm/ADT/SmallVector.cpp - 'Normally small' vectors ----------------===#
#
#                     The LLVM Compiler Infrastructure
#
# This file is distributed under the University of Illinois Open Source
# License. See LICENSE.TXT for details.
#
#===----------------------------------------------------------------------===#
#
# This file implements the SmallVector class.
#
#===----------------------------------------------------------------------===#

#include "llvm/SmallVector.h"
using namespace llvm

#/ grow_pod - This is an implementation of the grow() method which only works
#/ on POD-like datatypes and is out of line to reduce code duplication.
void SmallVectorBase.grow_pod(void *FirstEl, MinSizeInBytes,
                               size_t TSize)
    CurSizeBytes = size_in_bytes()
    NewCapacityInBytes = 2 * capacity_in_bytes() + TSize; # Always grow.
    if NewCapacityInBytes < MinSizeInBytes:
        NewCapacityInBytes = MinSizeInBytes


    void *NewElts
    if BeginX == FirstEl:
        NewElts = malloc(NewCapacityInBytes)

        # Copy the elements over.  No need to run dtors on PODs.
        memcpy(NewElts, self.BeginX, CurSizeBytes)

    else:
        # If self wasn't grown from the inline copy, the allocated space.
        NewElts = realloc(self.BeginX, NewCapacityInBytes)

    assert(NewElts and "Out of memory")

    self.EndX = (char*)NewElts+CurSizeBytes
    self.BeginX = NewElts
    self.CapacityX = (char*)self.BeginX + NewCapacityInBytes


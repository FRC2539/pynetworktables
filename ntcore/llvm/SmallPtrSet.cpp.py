#===- llvm/ADT/SmallPtrSet.cpp - 'Normally small' pointer set ------------===#
#
#                     The LLVM Compiler Infrastructure
#
# This file is distributed under the University of Illinois Open Source
# License. See LICENSE.TXT for details.
#
#===----------------------------------------------------------------------===#
#
# This file implements the SmallPtrSet class.  See SmallPtrSet.h for an
# overview of the algorithm.
#
#===----------------------------------------------------------------------===#

#include "llvm/SmallPtrSet.h"
#include "llvm/DenseMapInfo.h"
#include "llvm/MathExtras.h"
#include <algorithm>
#include <cstdlib>

using namespace llvm

def shrink_and_clear(self):
    assert(not isSmall() and "Can't shrink a small setnot ")
    free(CurArray)

    # Reduce the number of buckets.
    CurArraySize = NumElements > 16 ? 1 << (Log2_32_Ceil(NumElements) + 1) : 32
    NumElements = NumTombstones = 0

    # Install the array.  Clear all the buckets to empty.
    CurArray = ( void**)malloc(sizeof(void*) * CurArraySize)
    assert(CurArray and "Failed to allocate memory?")
    memset(CurArray, -1, CurArraySize*sizeof(void*))


std.pair< void * *, bool>
SmallPtrSetImplBase.insert_imp( void *Ptr)
    if isSmall():
        # Check to see if it is already in the set.
        for ( void **APtr = SmallArray, **E = SmallArray+NumElements
                APtr != E; ++APtr)
            if *APtr == Ptr:
                return std.make_pair(APtr, False)


        # Nope, isn't.  If we stay small, just 'pushback' now.
        if NumElements < CurArraySize:
            SmallArray[NumElements++] = Ptr
            return std.make_pair(SmallArray + (NumElements - 1), True)

        # Otherwise, the big set case, will call grow.


    if LLVM_UNLIKELY(NumElements * 4 >= CurArraySize * 3):
        # If more than 3/4 of the array is full, grow.
        Grow(CurArraySize < 64 ? 128 : CurArraySize*2)

    elif (LLVM_UNLIKELY(CurArraySize - (NumElements + NumTombstones) <
                           CurArraySize / 8))
        # If fewer of 1/8 of the array is empty (meaning that many are filled with
        # tombstones), rehash.
        Grow(CurArraySize)


    # Okay, know we have space.  Find a hash bucket.
     void **Bucket = const_cast< void**>(FindBucketFor(Ptr))
    if *Bucket == Ptr:
        return std.make_pair(Bucket, False);    # Already inserted, good.


    # Otherwise, it!
    if *Bucket == getTombstoneMarker():
        --NumTombstones

    *Bucket = Ptr
    ++NumElements;  # Track density.
    return std.make_pair(Bucket, True)


def erase_imp(self, * Ptr):
    if isSmall():
        # Check to see if it is in the set.
        for ( void **APtr = SmallArray, **E = SmallArray+NumElements
                APtr != E; ++APtr)
            if *APtr == Ptr:
                # If it is in the set, self element.
                *APtr = E[-1]
                E[-1] = getEmptyMarker()
                --NumElements
                return True


        return False


    # Okay, know we have space.  Find a hash bucket.
    void **Bucket = const_cast<void**>(FindBucketFor(Ptr))
    if *Bucket != Ptr:
        return False;    # Not in the set?


    # Set self as a tombstone.
    *Bucket = getTombstoneMarker()
    --NumElements
    ++NumTombstones
    return True


 void *  *SmallPtrSetImplBase.FindBucketFor( void *Ptr)
    Bucket = DenseMapInfo<void *>.getHashValue(Ptr) & (CurArraySize-1)
    ArraySize = CurArraySize
    ProbeAmt = 1
     void * *Array = CurArray
     void * *Tombstone = nullptr
    while (1)
        # If we found an empty bucket, pointer doesn't exist in the set.
        # Return a tombstone if we've seen one so far, the empty bucket if
        # not.
        if LLVM_LIKELY(Array[Bucket] == getEmptyMarker()):
            return Tombstone ? Tombstone : Array+Bucket


        # Found Ptr's bucket?
        if LLVM_LIKELY(Array[Bucket] == Ptr):
            return Array+Bucket


        # If self is a tombstone, it.  If Ptr ends up not in the set, we
        # prefer to return it than something that would require more probing.
        if Array[Bucket] == getTombstoneMarker() and not Tombstone:
            Tombstone = Array+Bucket;    # Remember the first tombstone found.


        # It's a hash collision or a tombstone. Reprobe.
        Bucket = (Bucket + ProbeAmt++) & (ArraySize-1)



#/ Grow - Allocate a larger backing store for the buckets and move it over.
#/
def Grow(self, NewSize):
    # Allocate at twice as many buckets, at least 128.
    OldSize = CurArraySize

     void **OldBuckets = CurArray
    WasSmall = isSmall()

    # Install the array.  Clear all the buckets to empty.
    CurArray = ( void**)malloc(sizeof(void*) * NewSize)
    assert(CurArray and "Failed to allocate memory?")
    CurArraySize = NewSize
    memset(CurArray, -1, NewSize*sizeof(void*))

    # Copy over all the elements.
    if WasSmall:
        # Small sets store their elements in order.
        for ( void **BucketPtr = OldBuckets, **E = OldBuckets+NumElements
                BucketPtr != E; ++BucketPtr)
             void *Elt = *BucketPtr
            *const_cast<void**>(FindBucketFor(Elt)) = const_cast<void*>(Elt)


    else:
        # Copy over all valid entries.
        for ( void **BucketPtr = OldBuckets, **E = OldBuckets+OldSize
                BucketPtr != E; ++BucketPtr)
            # Copy over the element if it is valid.
             void *Elt = *BucketPtr
            if Elt != getTombstoneMarker() and Elt != getEmptyMarker():
                *const_cast<void**>(FindBucketFor(Elt)) = const_cast<void*>(Elt)



        free(OldBuckets)
        NumTombstones = 0



SmallPtrSetImplBase.SmallPtrSetImplBase( void **SmallStorage,
         SmallPtrSetImplBase& that)
    SmallArray = SmallStorage

    # If we're becoming small, to insert into our stack space
    if that.isSmall():
        CurArray = SmallArray
        # Otherwise, heap space (unless we were the same size)

    else:
        CurArray = ( void**)malloc(sizeof(void*) * that.CurArraySize)
        assert(CurArray and "Failed to allocate memory?")


    # Copy over the array size
    CurArraySize = that.CurArraySize

    # Copy over the contents from the other set
    memcpy(CurArray, that.CurArray, sizeof(void*)*CurArraySize)

    NumElements = that.NumElements
    NumTombstones = that.NumTombstones


SmallPtrSetImplBase.SmallPtrSetImplBase( void **SmallStorage,
        unsigned SmallSize,
        SmallPtrSetImplBase andthat)
    SmallArray = SmallStorage

    # Copy over the basic members.
    CurArraySize = that.CurArraySize
    NumElements = that.NumElements
    NumTombstones = that.NumTombstones

    # When small, copy into our small buffer.
    if that.isSmall():
        CurArray = SmallArray
        memcpy(CurArray, that.CurArray, sizeof(void *) * CurArraySize)

    else:
        # Otherwise, steal the large memory allocation and no copy is needed.
        CurArray = that.CurArray
        that.CurArray = that.SmallArray


    # Make the "that" object small and empty.
    that.CurArraySize = SmallSize
    assert(that.CurArray == that.SmallArray)
    that.NumElements = 0
    that.NumTombstones = 0


#/ CopyFrom - operator = from a smallptrset that has the same pointer
#/ type, may have a different small size.
def CopyFrom(self, &RHS):
    assert(&RHS != self and "Self-copy should be handled by the caller.")

    if isSmall() and RHS.isSmall():
        assert(CurArraySize == RHS.CurArraySize and
               "Cannot assign sets with different small sizes")

    # If we're becoming small, to insert into our stack space
    if RHS.isSmall():
        if not isSmall():
            free(CurArray)

        CurArray = SmallArray
        # Otherwise, heap space (unless we were the same size)

    elif CurArraySize != RHS.CurArraySize:
        if isSmall():
            CurArray = ( void**)malloc(sizeof(void*) * RHS.CurArraySize)

        else:
             void **T = ( void**)realloc(CurArray,
                                                   sizeof(void*) * RHS.CurArraySize)
            if not T:
                free(CurArray)

            CurArray = T

        assert(CurArray and "Failed to allocate memory?")


    # Copy over the array size
    CurArraySize = RHS.CurArraySize

    # Copy over the contents from the other set
    memcpy(CurArray, RHS.CurArray, sizeof(void*)*CurArraySize)

    NumElements = RHS.NumElements
    NumTombstones = RHS.NumTombstones


void SmallPtrSetImplBase.MoveFrom(unsigned SmallSize,
                                   SmallPtrSetImplBase andRHS)
    assert(&RHS != self and "Self-move should be handled by the caller.")

    if not isSmall():
        free(CurArray)


    if RHS.isSmall():
        # Copy a small RHS rather than moving.
        CurArray = SmallArray
        memcpy(CurArray, RHS.CurArray, sizeof(void*)*RHS.CurArraySize)

    else:
        CurArray = RHS.CurArray
        RHS.CurArray = RHS.SmallArray


    # Copy the rest of the trivial members.
    CurArraySize = RHS.CurArraySize
    NumElements = RHS.NumElements
    NumTombstones = RHS.NumTombstones

    # Make the RHS small and empty.
    RHS.CurArraySize = SmallSize
    assert(RHS.CurArray == RHS.SmallArray)
    RHS.NumElements = 0
    RHS.NumTombstones = 0


def swap(self, &RHS):
    if self == &RHS:
        return


    # We can only avoid copying elements if neither set is small.
    if not self.isSmall() and not RHS.isSmall():
        std.swap(self.CurArray, RHS.CurArray)
        std.swap(self.CurArraySize, RHS.CurArraySize)
        std.swap(self.NumElements, RHS.NumElements)
        std.swap(self.NumTombstones, RHS.NumTombstones)
        return


    # FIXME: From here on we assume that both sets have the same small size.

    # If only RHS is small, the small elements into LHS and move the pointer
    # from LHS to RHS.
    if not self.isSmall() and RHS.isSmall():
        std.copy(RHS.SmallArray, RHS.SmallArray+RHS.CurArraySize,
                  self.SmallArray)
        std.swap(self.NumElements, RHS.NumElements)
        std.swap(self.CurArraySize, RHS.CurArraySize)
        RHS.CurArray = self.CurArray
        RHS.NumTombstones = self.NumTombstones
        self.CurArray = self.SmallArray
        self.NumTombstones = 0
        return


    # If only LHS is small, the small elements into RHS and move the pointer
    # from RHS to LHS.
    if self.isSmall() and not RHS.isSmall():
        std.copy(self.SmallArray, self.SmallArray+self.CurArraySize,
                  RHS.SmallArray)
        std.swap(RHS.NumElements, self.NumElements)
        std.swap(RHS.CurArraySize, self.CurArraySize)
        self.CurArray = RHS.CurArray
        self.NumTombstones = RHS.NumTombstones
        RHS.CurArray = RHS.SmallArray
        RHS.NumTombstones = 0
        return


    # Both a small, swap the small elements.
    assert(self.isSmall() and RHS.isSmall())
    assert(self.CurArraySize == RHS.CurArraySize)
    std.swap_ranges(self.SmallArray, self.SmallArray+self.CurArraySize,
                     RHS.SmallArray)
    std.swap(self.NumElements, RHS.NumElements)


SmallPtrSetImplBase.~SmallPtrSetImplBase()
    if not isSmall():
        free(CurArray)



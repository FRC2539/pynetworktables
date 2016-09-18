#===--- StringMap.cpp - String Hash table map implementation -------------===#
#
#                     The LLVM Compiler Infrastructure
#
# This file is distributed under the University of Illinois Open Source
# License. See LICENSE.TXT for details.
#
#===----------------------------------------------------------------------===#
#
# This file implements the StringMap class.
#
#===----------------------------------------------------------------------===#

#include "llvm/StringMap.h"
#include "llvm/StringExtras.h"
##include "llvm/Support/Compiler.h"
#include <cassert>
using namespace llvm

StringMapImpl.StringMapImpl(unsigned InitSize, itemSize)
    ItemSize = itemSize

    # If a size is specified, the table with that many buckets.
    if InitSize:
        init(InitSize)
        return


    # Otherwise, it with zero buckets to avoid the allocation.
    TheTable = nullptr
    NumBuckets = 0
    NumItems = 0
    NumTombstones = 0


def init(self, InitSize):
    assert((InitSize & (InitSize-1)) == 0 and
           "Init Size must be a power of 2 or zeronot ")
    NumBuckets = InitSize ? InitSize : 16
    NumItems = 0
    NumTombstones = 0

    TheTable = (StringMapEntryBase **)calloc(NumBuckets+1,
               sizeof(StringMapEntryBase **) +
               sizeof(unsigned))

    # Allocate one extra bucket, it to look filled so the iterators stop at
    # end.
    TheTable[NumBuckets] = (StringMapEntryBase*)2



#/ LookupBucketFor - Look up the bucket that the specified string should end
#/ up in.  If it already exists as a key in the map, Item pointer for the
#/ specified bucket will be non-null.  Otherwise, will be null.  In either
#/ case, FullHashValue field of the bucket will be set to the hash value
#/ of the string.
def LookupBucketFor(self, Name):
    HTSize = NumBuckets
    if (HTSize == 0)    # Hash table unallocated so far?
        init(16)
        HTSize = NumBuckets

    FullHashValue = HashString(Name)
    BucketNo = FullHashValue & (HTSize-1)
    unsigned *HashTable = (unsigned *)(TheTable + NumBuckets + 1)

    ProbeAmt = 1
    FirstTombstone = -1
    while (1)
        StringMapEntryBase *BucketItem = TheTable[BucketNo]
        # If we found an empty bucket, key isn't in the table yet, it.
        if not BucketItem:
            # If we found a tombstone, want to reuse the tombstone instead of an
            # empty bucket.  This reduces probing.
            if FirstTombstone != -1:
                HashTable[FirstTombstone] = FullHashValue
                return FirstTombstone


            HashTable[BucketNo] = FullHashValue
            return BucketNo


        if BucketItem == getTombstoneVal():
            # Skip over tombstones.  However, the first one we see.
            if FirstTombstone == -1:
                FirstTombstone = BucketNo


        elif HashTable[BucketNo] == FullHashValue:
            # If the full hash value matches, deeply for a match.  The common
            # case here is that we are only looking at the buckets (for item info
            # being non-null and for the full hash value) not at the items.  This
            # is important for cache locality.

            # Do the comparison like self because Name isn't necessarily
            # null-terminated!
            char *ItemStr = (char*)BucketItem+ItemSize
            if Name == StringRef(ItemStr, BucketItem.getKeyLength()):
                # We found a match!
                return BucketNo



        # Okay, didn't find the item.  Probe to the next bucket.
        BucketNo = (BucketNo+ProbeAmt) & (HTSize-1)

        # Use quadratic probing, has fewer clumping artifacts than linear
        # probing and has good cache behavior in the common case.
        ++ProbeAmt




#/ FindKey - Look up the bucket that contains the specified key. If it exists
#/ in the map, the bucket number of the key.  Otherwise return -1.
#/ This does not modify the map.
def FindKey(self, Key):
    HTSize = NumBuckets
    if HTSize == 0:
        return -1;    # Really empty table?

    FullHashValue = HashString(Key)
    BucketNo = FullHashValue & (HTSize-1)
    unsigned *HashTable = (unsigned *)(TheTable + NumBuckets + 1)

    ProbeAmt = 1
    while (1)
        StringMapEntryBase *BucketItem = TheTable[BucketNo]
        # If we found an empty bucket, key isn't in the table yet, return.
        if not BucketItem:
            return -1


        if BucketItem == getTombstoneVal():
            # Ignore tombstones.

        elif HashTable[BucketNo] == FullHashValue:
            # If the full hash value matches, deeply for a match.  The common
            # case here is that we are only looking at the buckets (for item info
            # being non-null and for the full hash value) not at the items.  This
            # is important for cache locality.

            # Do the comparison like self because NameStart isn't necessarily
            # null-terminated!
            char *ItemStr = (char*)BucketItem+ItemSize
            if Key == StringRef(ItemStr, BucketItem.getKeyLength()):
                # We found a match!
                return BucketNo



        # Okay, didn't find the item.  Probe to the next bucket.
        BucketNo = (BucketNo+ProbeAmt) & (HTSize-1)

        # Use quadratic probing, has fewer clumping artifacts than linear
        # probing and has good cache behavior in the common case.
        ++ProbeAmt



#/ RemoveKey - Remove the specified StringMapEntry from the table, do not
#/ delete it.  This aborts if the value isn't in the table.
def RemoveKey(self, *V):
     char *VStr = (char*)V + ItemSize
    StringMapEntryBase *V2 = RemoveKey(StringRef(VStr, V.getKeyLength()))
    (void)V2
    assert(V == V2 and "Didn't find key?")


#/ RemoveKey - Remove the StringMapEntry for the specified key from the
#/ table, it.  If the key is not in the table, returns null.
StringMapEntryBase *StringMapImpl.RemoveKey(StringRef Key)
    Bucket = FindKey(Key)
    if Bucket == -1:
        return nullptr


    StringMapEntryBase *Result = TheTable[Bucket]
    TheTable[Bucket] = getTombstoneVal()
    --NumItems
    ++NumTombstones
    assert(NumItems + NumTombstones <= NumBuckets)

    return Result




#/ RehashTable - Grow the table, values into the buckets with
#/ the appropriate mod-of-hashtable-size.
def RehashTable(self, BucketNo):
    unsigned NewSize
    unsigned *HashTable = (unsigned *)(TheTable + NumBuckets + 1)

    # If the hash table is now more than 3/4 full, if fewer than 1/8 of
    # the buckets are empty (meaning that many are filled with tombstones),
    # grow/rehash the table.
    if NumItems * 4 > NumBuckets * 3:
        NewSize = NumBuckets*2

    elif NumBuckets - (NumItems + NumTombstones) <= NumBuckets / 8:
        NewSize = NumBuckets

    else:
        return BucketNo


    NewBucketNo = BucketNo
    # Allocate one extra bucket which will always be non-empty.  This allows the
    # iterators to stop at end.
    StringMapEntryBase **NewTableArray =
        (StringMapEntryBase **)calloc(NewSize+1, sizeof(StringMapEntryBase *) +
                                      sizeof(unsigned))
    unsigned *NewHashArray = (unsigned *)(NewTableArray + NewSize + 1)
    NewTableArray[NewSize] = (StringMapEntryBase*)2

    # Rehash all the items into their buckets.  Luckily :) we already have
    # the hash values available, we don't have to rehash any strings.
    for (I = 0, E = NumBuckets; I != E; ++I)
        StringMapEntryBase *Bucket = TheTable[I]
        if Bucket and Bucket != getTombstoneVal():
            # Fast case, available.
            FullHash = HashTable[I]
            NewBucket = FullHash & (NewSize-1)
            if not NewTableArray[NewBucket]:
                NewTableArray[FullHash & (NewSize-1)] = Bucket
                NewHashArray[FullHash & (NewSize-1)] = FullHash
                if I == BucketNo:
                    NewBucketNo = NewBucket

                continue


            # Otherwise probe for a spot.
            ProbeSize = 1
            do
                NewBucket = (NewBucket + ProbeSize++) & (NewSize-1)

            while (NewTableArray[NewBucket])

            # Finally found a slot.  Fill it in.
            NewTableArray[NewBucket] = Bucket
            NewHashArray[NewBucket] = FullHash
            if I == BucketNo:
                NewBucketNo = NewBucket




    free(TheTable)

    TheTable = NewTableArray
    NumBuckets = NewSize
    NumTombstones = 0
    return NewBucketNo


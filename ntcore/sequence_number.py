'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "SequenceNumber.h"




def lt(l, r):
    if l < r:
        return (r - l) < (1 << 15)

    elif l > r:
        return (l - r) > (1 << 15)

    else:
        return False





def gt(l, r):
    if l < r:
        return (r - l) > (1 << 15)

    elif l > r:
        return (l - r) < (1 << 15)

    else:
        return False


def cmp(l, r):
    print("L: %5d; R: %5d, LT: %5s: GT: %5s" % (
          l, r, lt(l, r), gt(l, r)))


cmp(5, 10)
cmp(10, 5)
print()

cmp(5, 40000)
cmp(40000, 5)
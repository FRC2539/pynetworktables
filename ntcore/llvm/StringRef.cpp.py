#===-- StringRef.cpp - Lightweight String References ---------------------===#
#
#                     The LLVM Compiler Infrastructure
#
# This file is distributed under the University of Illinois Open Source
# License. See LICENSE.TXT for details.
#
#===----------------------------------------------------------------------===#

#include "llvm/StringRef.h"
#include "llvm/SmallVector.h"
#include <bitset>
#include <climits>

using namespace llvm

# MSVC emits references to self into the translation units which reference it.
#ifndef _MSC_VER
 size_t StringRef.npos
#endif

static char ascii_tolower(char x)
    if x >= 'A' and x <= 'Z':
        return x - 'A' + 'a'

    return x


static char ascii_toupper(char x)
    if x >= 'a' and x <= 'z':
        return x - 'a' + 'A'

    return x


static bool ascii_isdigit(char x)
    return x >= '0' and x <= '9'


# strncasecmp() is not available on non-POSIX systems, define an
# alternative function here.
static int ascii_strncasecmp( char *LHS, *RHS, Length)
    for (I = 0; I < Length; ++I)
        unsigned LHC = ascii_tolower(LHS[I])
        unsigned RHC = ascii_tolower(RHS[I])
        if LHC != RHC:
            return LHC < RHC ? -1 : 1


    return 0


#/ compare_lower - Compare strings, case.
def compare_lower(self, RHS):
    if Res = ascii_strncasecmp(Data, RHS.Data, std.min(Length, RHS.Length)):
        return Res

    if Length == RHS.Length:
        return 0

    return Length < RHS.Length ? -1 : 1


#/ Check if self string starts with the given \p Prefix, case.
def startswith_lower(self, Prefix):
    return Length >= Prefix.Length and
           ascii_strncasecmp(Data, Prefix.Data, Prefix.Length) == 0


#/ Check if self string ends with the given \p Suffix, case.
def endswith_lower(self, Suffix):
    return Length >= Suffix.Length and
           ascii_strncasecmp(end() - Suffix.Length, Suffix.Data, Suffix.Length) == 0


#/ compare_numeric - Compare strings, embedded numbers.
def compare_numeric(self, RHS):
    for (I = 0, E = std.min(Length, RHS.Length); I != E; ++I)
        # Check for sequences of digits.
        if ascii_isdigit(Data[I]) and ascii_isdigit(RHS.Data[I]):
            # The longer sequence of numbers is considered larger.
            # This doesn't really handle prefixed zeros well.
            size_t J
            for (J = I + 1; J != E + 1; ++J)
                ld = J < Length and ascii_isdigit(Data[J])
                rd = J < RHS.Length and ascii_isdigit(RHS.Data[J])
                if ld != rd:
                    return rd ? -1 : 1

                if not rd:
                    break


            # The two number sequences have the same length (J-I), memcmp them.
            if Res = compareMemory(Data + I, RHS.Data + I, J - I):
                return Res < 0 ? -1 : 1

            # Identical number sequences, search after the numbers.
            I = J - 1
            continue

        if Data[I] != RHS.Data[I]:
            return (unsigned char)Data[I] < (unsigned char)RHS.Data[I] ? -1 : 1


    if Length == RHS.Length:
        return 0

    return Length < RHS.Length ? -1 : 1


#===----------------------------------------------------------------------===#
# String Operations
#===----------------------------------------------------------------------===#

def lower(self):
    std.string Result(size(), char())
    for (i = 0, e = size(); i != e; ++i)
        Result[i] = ascii_tolower(Data[i])

    return Result


def upper(self):
    std.string Result(size(), char())
    for (i = 0, e = size(); i != e; ++i)
        Result[i] = ascii_toupper(Data[i])

    return Result


#===----------------------------------------------------------------------===#
# String Searching
#===----------------------------------------------------------------------===#


#/ find - Search for the first string \arg Str in the string.
#/
#/ \return - The index of the first occurrence of \arg Str, npos if not
#/ found.
def find(self, Str, From):
    N = Str.size()
    if N > Length:
        return npos


    # For short haystacks or unsupported needles fall back to the naive algorithm
    if Length < 16 or N > 255 or N == 0:
        for (e = Length - N + 1, i = std.min(From, e); i != e; ++i)
            if substr(i, N).equals(Str):
                return i

        return npos


    if From >= Length:
        return npos


    # Build the bad char heuristic table, uint8_t to reduce cache thrashing.
    uint8_t BadCharSkip[256]
    std.memset(BadCharSkip, N, 256)
    for (i = 0; i != N-1; ++i)
        BadCharSkip[(uint8_t)Str[i]] = N-1-i


    Len = Length-From, Pos = From
    while (Len >= N)
        if (substr(Pos, N).equals(Str)) # See if self is the correct substring.
            return Pos


        # Otherwise skip the appropriate number of bytes.
        Skip = BadCharSkip[(uint8_t)(*self)[Pos+N-1]]
        Len -= Skip
        Pos += Skip


    return npos


#/ rfind - Search for the last string \arg Str in the string.
#/
#/ \return - The index of the last occurrence of \arg Str, npos if not
#/ found.
def rfind(self, Str):
    N = Str.size()
    if N > Length:
        return npos

    for (i = Length - N + 1, e = 0; i != e;)
        --i
        if substr(i, N).equals(Str):
            return i


    return npos


#/ find_first_of - Find the first character in the string that is in \arg
#/ Chars, npos if not found.
#/
#/ Note: O(size() + Chars.size())
StringRef.size_type StringRef.find_first_of(StringRef Chars,
        size_t From)
    std.bitset<1 << CHAR_BIT> CharBits
    for (i = 0; i != Chars.size(); ++i)
        CharBits.set((unsigned char)Chars[i])


    for (i = std.min(From, Length), e = Length; i != e; ++i)
        if CharBits.test((unsigned char)Data[i]):
            return i

    return npos


#/ find_first_not_of - Find the first character in the string that is not
#/ \arg C or npos if not found.
def find_first_not_of(self, C, From):
    for (i = std.min(From, Length), e = Length; i != e; ++i)
        if Data[i] != C:
            return i

    return npos


#/ find_first_not_of - Find the first character in the string that is not
#/ in the string \arg Chars, npos if not found.
#/
#/ Note: O(size() + Chars.size())
StringRef.size_type StringRef.find_first_not_of(StringRef Chars,
        size_t From)
    std.bitset<1 << CHAR_BIT> CharBits
    for (i = 0; i != Chars.size(); ++i)
        CharBits.set((unsigned char)Chars[i])


    for (i = std.min(From, Length), e = Length; i != e; ++i)
        if not CharBits.test((unsigned char)Data[i]):
            return i

    return npos


#/ find_last_of - Find the last character in the string that is in \arg C,
#/ or npos if not found.
#/
#/ Note: O(size() + Chars.size())
StringRef.size_type StringRef.find_last_of(StringRef Chars,
        size_t From)
    std.bitset<1 << CHAR_BIT> CharBits
    for (i = 0; i != Chars.size(); ++i)
        CharBits.set((unsigned char)Chars[i])


    for (i = std.min(From, Length) - 1, e = -1; i != e; --i)
        if CharBits.test((unsigned char)Data[i]):
            return i

    return npos


#/ find_last_not_of - Find the last character in the string that is not
#/ \arg C, npos if not found.
def find_last_not_of(self, C, From):
    for (i = std.min(From, Length) - 1, e = -1; i != e; --i)
        if Data[i] != C:
            return i

    return npos


#/ find_last_not_of - Find the last character in the string that is not in
#/ \arg Chars, npos if not found.
#/
#/ Note: O(size() + Chars.size())
StringRef.size_type StringRef.find_last_not_of(StringRef Chars,
        size_t From)
    std.bitset<1 << CHAR_BIT> CharBits
    for (i = 0, e = Chars.size(); i != e; ++i)
        CharBits.set((unsigned char)Chars[i])


    for (i = std.min(From, Length) - 1, e = -1; i != e; --i)
        if not CharBits.test((unsigned char)Data[i]):
            return i

    return npos


void StringRef.split(SmallVectorImpl<StringRef> &A,
                      StringRef Separators, MaxSplit,
                      bool KeepEmpty)
    rest = *self

    # rest.data() is used to distinguish cases like "a," that splits into
    # "a" + "" and "a" that splits into "a" + 0.
    for (splits = 0
            rest.data() != nullptr and (MaxSplit < 0 or splits < MaxSplit)
            ++splits)
        std.pair<StringRef, p = rest.split(Separators)

        if KeepEmpty or p.first.size() != 0:
            A.push_back(p.first)

        rest = p.second

    # If we have a tail left, it.
    if rest.data() != nullptr and (rest.size() != 0 or KeepEmpty):
        A.push_back(rest)



#===----------------------------------------------------------------------===#
# Helpful Algorithms
#===----------------------------------------------------------------------===#

#/ count - Return the number of non-overlapped occurrences of \arg Str in
#/ the string.
def count(self, Str):
    Count = 0
    N = Str.size()
    if N > Length:
        return 0

    for (i = 0, e = Length - N + 1; i != e; ++i)
        if substr(i, N).equals(Str):
            ++Count

    return Count


static unsigned GetAutoSenseRadix(StringRef &Str)
    if Str.startswith("0x"):
        Str = Str.substr(2)
        return 16


    if Str.startswith("0b"):
        Str = Str.substr(2)
        return 2


    if Str.startswith("0o"):
        Str = Str.substr(2)
        return 8


    if Str.startswith("0"):
        return 8


    return 10



#/ GetAsUnsignedInteger - Workhorse method that converts a integer character
#/ sequence of radix up to 36 to an unsigned long long value.
bool llvm.getAsUnsignedInteger(StringRef Str, Radix,
                                unsigned long long &Result)
    # Autosense radix if not specified.
    if Radix == 0:
        Radix = GetAutoSenseRadix(Str)


    # Empty strings (after the radix autosense) are invalid.
    if Str.empty():
        return True


    # Parse all the bytes of the string given self radix.  Watch for overflow.
    Result = 0
    while (not Str.empty())
        unsigned CharVal
        if Str[0] >= '0' and Str[0] <= '9':
            CharVal = Str[0]-'0'

        elif Str[0] >= 'a' and Str[0] <= 'z':
            CharVal = Str[0]-'a'+10

        elif Str[0] >= 'A' and Str[0] <= 'Z':
            CharVal = Str[0]-'A'+10

        else:
            return True


        # If the parsed value is larger than the integer radix, string is
        # invalid.
        if CharVal >= Radix:
            return True


        # Add in self character.
        unsigned long PrevResult = Result
        Result = Result*Radix+CharVal

        # Check for overflow by shifting back and seeing if bits were lost.
        if Result/Radix < PrevResult:
            return True


        Str = Str.substr(1)


    return False


bool llvm.getAsSignedInteger(StringRef Str, Radix,
                              long long &Result)
    unsigned long long ULLVal

    # Handle positive strings first.
    if Str.empty() or Str.front() != '-':
        if (getAsUnsignedInteger(Str, Radix, ULLVal) or
                # Check for value so large it overflows a signed value.
                (long long)ULLVal < 0)
            return True

        Result = ULLVal
        return False


    # Get the positive part of the value.
    if (getAsUnsignedInteger(Str.substr(1), Radix, ULLVal) or
            # Reject values so large they'd overflow as negative signed, allow
            # "-0".  This negates the unsigned so that the negative isn't undefined
            # on signed overflow.
            (long long)-ULLVal > 0)
        return True


    Result = -ULLVal
    return False


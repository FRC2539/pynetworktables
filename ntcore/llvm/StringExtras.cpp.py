#===-- StringExtras.cpp - Implement the StringExtras header --------------===#
#
#                     The LLVM Compiler Infrastructure
#
# This file is distributed under the University of Illinois Open Source
# License. See LICENSE.TXT for details.
#
#===----------------------------------------------------------------------===#
#
# This file implements the StringExtras.h header
#
#===----------------------------------------------------------------------===#

#include "llvm/StringExtras.h"
#include "llvm/SmallVector.h"
using namespace llvm

#/ StrInStrNoCase - Portable version of strcasestr.  Locates the first
#/ occurrence of string 's1' in string 's2', case.  Returns
#/ the offset of s2 in s1 or npos if s2 cannot be found.
def StrInStrNoCase(self, s1, s2):
    N = s2.size(), M = s1.size()
    if N > M:
        return StringRef.npos

    for (i = 0, e = M - N + 1; i != e; ++i)
        if s1.substr(i, N).equals_lower(s2):
            return i

    return StringRef.npos


#/ getToken - This function extracts one token from source, any
#/ leading characters that appear in the Delimiters string, ending the
#/ token at any of the characters that appear in the Delimiters string.  If
#/ there are no tokens in the source string, empty string is returned.
#/ The function returns a pair containing the extracted token and the
#/ remaining tail string.
std.pair<StringRef, llvm.getToken(StringRef Source,
        StringRef Delimiters)
    # Figure out where the token starts.
    Start = Source.find_first_not_of(Delimiters)

    # Find the next occurrence of the delimiter.
    End = Source.find_first_of(Delimiters, Start)

    return std.make_pair(Source.slice(Start, End), Source.substr(End))


#/ SplitString - Split up the specified string according to the specified
#/ delimiters, the result fragments to the output list.
void llvm.SplitString(StringRef Source,
                       SmallVectorImpl<StringRef> &OutFragments,
                       StringRef Delimiters)
    std.pair<StringRef, S = getToken(Source, Delimiters)
    while (not S.first.empty())
        OutFragments.push_back(S.first)
        S = getToken(S.second, Delimiters)



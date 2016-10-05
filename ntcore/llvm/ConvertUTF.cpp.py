'''===--- ConvertUTF.c - Universal Character Names conversions ---------------===
 *
 *                     The LLVM Compiler Infrastructure
 *
 * This file is distributed under the University of Illinois Open Source
 * License. See LICENSE.TXT for details.
 *
 *===------------------------------------------------------------------------='''
'''
 * Copyright 2001-2004 Unicode, Inc.
 *
 * Disclaimer
 *
 * This source code is provided as is by Unicode, Inc. No claims are
 * made as to fitness for any particular purpose. No warranties of any
 * kind are expressed or implied. The recipient agrees to determine
 * applicability of information provided. If self file has been
 * purchased on magnetic or optical media from Unicode, Inc., the
 * sole remedy for any claim will be exchange of defective media
 * within 90 days of receipt.
 *
 * Limitations on Rights to Redistribute This Code
 *
 * Unicode, Inc. hereby grants the right to freely use the information
 * supplied in self file in the creation of products supporting the
 * Unicode Standard, to make copies of self file in any form
 * for internal or external distribution as long as self notice
 * remains attached.
 '''

''' ---------------------------------------------------------------------

    Conversions between UTF32, UTF-16, UTF-8. Source code file.
    Author: Mark E. Davis, 1994.
    Rev History: Rick McGowan, & updates May 2001.
    Sept 2001: fixed  & error conditions per
        mods suggested by S. Parent & A. Lillich.
    June 2002: Tim Dodd added detection and handling of incomplete
        source sequences, error detection, casts
        to eliminate compiler warnings.
    July 2003: slight mods to back out aggressive FFFE detection.
    Jan 2004: updated switches in from-UTF8 conversions.
    Oct 2004: updated to use UNI_MAX_LEGAL_UTF32 in UTF-32 conversions.

    See the header file "ConvertUTF.h" for complete documentation.

------------------------------------------------------------------------ '''


#include "llvm/ConvertUTF.h"
#ifdef CVTUTF_DEBUG
#include <stdio.h>
#endif
#include <assert.h>

static  halfShift = 10; ''' used for shifting by 10 bits '''

static  halfBase = 0x0010000UL
static  halfMask = 0x3FFUL

#define UNI_SUR_HIGH_START  (UTF32)0xD800
#define UNI_SUR_HIGH_END    (UTF32)0xDBFF
#define UNI_SUR_LOW_START   (UTF32)0xDC00
#define UNI_SUR_LOW_END     (UTF32)0xDFFF

''' --------------------------------------------------------------------- '''

'''
 * Index into the table below with the first byte of a UTF-8 sequence to
 * get the number of trailing bytes that are supposed to follow it.
 * Note that *legal* UTF-8 values can't have 4 or 5-bytes. The table is
 * left as-is for anyone who may want to do such conversion, was
 * allowed in earlier algorithms.
 '''
static  char trailingBytesForUTF8[256] =
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
    2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2, 3,3,3,3,3,3,3,3,4,4,4,4,5,5,5,5


'''
 * Magic values subtracted from a buffer value during UTF8 conversion.
 * This table contains as many values as there might be trailing bytes
 * in a UTF-8 sequence.
 '''
static  UTF32 offsetsFromUTF8[6] = { 0x00000000UL, 0x00003080UL, 0x000E2080UL,
                                          0x03C82080UL, 0xFA082080UL, 0x82082080UL


'''
 * Once the bits are split out into bytes of UTF-8, is a mask OR-ed
 * into the first byte, on how many bytes follow.  There are
 * as many entries in self table as there are UTF-8 sequence types.
 * (I.e., byte sequence, byte... etc.). Remember that sequencs
 * for *legal* UTF-8 will be 4 or fewer bytes total.
 '''
static  UTF8 firstByteMark[7] = { 0x00, 0x00, 0xC0, 0xE0, 0xF0, 0xF8, 0xFC

''' --------------------------------------------------------------------- '''

''' The interface converts a whole buffer to avoid function-call overhead.
 * Constants have been gathered. Loops & conditionals have been removed as
 * much as possible for efficiency, favor of drop-through switches.
 * (See "Note A" at the bottom of the file for equivalent code.)
 * If your compiler supports it, the "isLegalUTF8" call can be turned
 * into an inline function.
 '''

extern "C"    ''' --------------------------------------------------------------------- '''

    ConversionResult ConvertUTF32toUTF16 (
         UTF32** sourceStart, sourceEnd,
        UTF16** targetStart, targetEnd, flags)
        result = conversionOK
         source = *sourceStart
        target = *targetStart
        while (source < sourceEnd)
            UTF32 ch
            if target >= targetEnd:
                result = targetExhausted
                break

            ch = *source++
            if (ch <= UNI_MAX_BMP)   ''' Target is a character <= 0xFFFF '''
                ''' UTF-16 surrogate values are illegal in UTF-32; 0xffff or 0xfffe are both reserved values '''
                if ch >= UNI_SUR_HIGH_START and ch <= UNI_SUR_LOW_END:
                    if flags == strictConversion:
                        --source; ''' return to the illegal value itself '''
                        result = sourceIllegal
                        break

                    else:
                        *target++ = UNI_REPLACEMENT_CHAR


                else:
                    *target++ = (UTF16)ch; ''' normal case '''


            elif ch > UNI_MAX_LEGAL_UTF32:
                if flags == strictConversion:
                    result = sourceIllegal

                else:
                    *target++ = UNI_REPLACEMENT_CHAR


            else:
                ''' target is a character in range 0xFFFF - 0x10FFFF. '''
                if target + 1 >= targetEnd:
                    --source; ''' Back up source pointernot  '''
                    result = targetExhausted
                    break

                ch -= halfBase
                *target++ = (UTF16)((ch >> halfShift) + UNI_SUR_HIGH_START)
                *target++ = (UTF16)((ch & halfMask) + UNI_SUR_LOW_START)


        *sourceStart = source
        *targetStart = target
        return result


    ''' --------------------------------------------------------------------- '''

    ConversionResult ConvertUTF16toUTF32 (
         UTF16** sourceStart, sourceEnd,
        UTF32** targetStart, targetEnd, flags)
        result = conversionOK
         source = *sourceStart
        target = *targetStart
        UTF32 ch, ch2
        while (source < sourceEnd)
             oldSource = source; '''  In case we have to back up because of target overflow. '''
            ch = *source++
            ''' If we have a surrogate pair, to UTF32 first. '''
            if ch >= UNI_SUR_HIGH_START and ch <= UNI_SUR_HIGH_END:
                ''' If the 16 bits following the high surrogate are in the source buffer... '''
                if source < sourceEnd:
                    ch2 = *source
                    ''' If it's a low surrogate, to UTF32. '''
                    if ch2 >= UNI_SUR_LOW_START and ch2 <= UNI_SUR_LOW_END:
                        ch = ((ch - UNI_SUR_HIGH_START) << halfShift)
                             + (ch2 - UNI_SUR_LOW_START) + halfBase
                        ++source

                    elif (flags == strictConversion)     ''' it's an unpaired high surrogate '''
                        --source; ''' return to the illegal value itself '''
                        result = sourceIllegal
                        break


                else     ''' We don't have the 16 bits following the high surrogate. '''
                    --source; ''' return to the high surrogate '''
                    result = sourceExhausted
                    break


            elif flags == strictConversion:
                ''' UTF-16 surrogate values are illegal in UTF-32 '''
                if ch >= UNI_SUR_LOW_START and ch <= UNI_SUR_LOW_END:
                    --source; ''' return to the illegal value itself '''
                    result = sourceIllegal
                    break


            if target >= targetEnd:
                source = oldSource; ''' Back up source pointernot  '''
                result = targetExhausted
                break

            *target++ = ch

        *sourceStart = source
        *targetStart = target
#ifdef CVTUTF_DEBUG
        if result == sourceIllegal:
            fprintf(stderr, "ConvertUTF16toUTF32 illegal seq 0x%04x,%04x\n", ch, ch2)
            fflush(stderr)

#endif
        return result

    ConversionResult ConvertUTF16toUTF8 (
         UTF16** sourceStart, sourceEnd,
        UTF8** targetStart, targetEnd, flags)
        result = conversionOK
         source = *sourceStart
        target = *targetStart
        while (source < sourceEnd)
            UTF32 ch
            unsigned bytesToWrite = 0
             byteMask = 0xBF
             byteMark = 0x80
             oldSource = source; ''' In case we have to back up because of target overflow. '''
            ch = *source++
            ''' If we have a surrogate pair, to UTF32 first. '''
            if ch >= UNI_SUR_HIGH_START and ch <= UNI_SUR_HIGH_END:
                ''' If the 16 bits following the high surrogate are in the source buffer... '''
                if source < sourceEnd:
                    ch2 = *source
                    ''' If it's a low surrogate, to UTF32. '''
                    if ch2 >= UNI_SUR_LOW_START and ch2 <= UNI_SUR_LOW_END:
                        ch = ((ch - UNI_SUR_HIGH_START) << halfShift)
                             + (ch2 - UNI_SUR_LOW_START) + halfBase
                        ++source

                    elif (flags == strictConversion)     ''' it's an unpaired high surrogate '''
                        --source; ''' return to the illegal value itself '''
                        result = sourceIllegal
                        break


                else     ''' We don't have the 16 bits following the high surrogate. '''
                    --source; ''' return to the high surrogate '''
                    result = sourceExhausted
                    break


            elif flags == strictConversion:
                ''' UTF-16 surrogate values are illegal in UTF-32 '''
                if ch >= UNI_SUR_LOW_START and ch <= UNI_SUR_LOW_END:
                    --source; ''' return to the illegal value itself '''
                    result = sourceIllegal
                    break


            ''' Figure out how many bytes the result will require '''
            if ch < (UTF32)0x80:
                bytesToWrite = 1

            elif ch < (UTF32)0x800:
                bytesToWrite = 2

            elif ch < (UTF32)0x10000:
                bytesToWrite = 3

            elif ch < (UTF32)0x110000:
                bytesToWrite = 4

            else:
                bytesToWrite = 3
                ch = UNI_REPLACEMENT_CHAR


            target += bytesToWrite
            if target > targetEnd:
                source = oldSource; ''' Back up source pointernot  '''
                target -= bytesToWrite
                result = targetExhausted
                break

            switch (bytesToWrite)   ''' note: everything falls through. '''
            case 4:
                *--target = (UTF8)((ch | byteMark) & byteMask)
                ch >>= 6
            case 3:
                *--target = (UTF8)((ch | byteMark) & byteMask)
                ch >>= 6
            case 2:
                *--target = (UTF8)((ch | byteMark) & byteMask)
                ch >>= 6
            case 1:
                *--target =  (UTF8)(ch | firstByteMark[bytesToWrite])

            target += bytesToWrite

        *sourceStart = source
        *targetStart = target
        return result


    ''' --------------------------------------------------------------------- '''

    ConversionResult ConvertUTF32toUTF8 (
         UTF32** sourceStart, sourceEnd,
        UTF8** targetStart, targetEnd, flags)
        result = conversionOK
         source = *sourceStart
        target = *targetStart
        while (source < sourceEnd)
            UTF32 ch
            unsigned bytesToWrite = 0
             byteMask = 0xBF
             byteMark = 0x80
            ch = *source++
            if flags == strictConversion :
                ''' UTF-16 surrogate values are illegal in UTF-32 '''
                if ch >= UNI_SUR_HIGH_START and ch <= UNI_SUR_LOW_END:
                    --source; ''' return to the illegal value itself '''
                    result = sourceIllegal
                    break


            '''
             * Figure out how many bytes the result will require. Turn any
             * illegally large UTF32 things (> Plane 17) into replacement chars.
             '''
            if ch < (UTF32)0x80:
                bytesToWrite = 1

            elif ch < (UTF32)0x800:
                bytesToWrite = 2

            elif ch < (UTF32)0x10000:
                bytesToWrite = 3

            elif ch <= UNI_MAX_LEGAL_UTF32:
                bytesToWrite = 4

            else:
                bytesToWrite = 3
                ch = UNI_REPLACEMENT_CHAR
                result = sourceIllegal


            target += bytesToWrite
            if target > targetEnd:
                --source; ''' Back up source pointernot  '''
                target -= bytesToWrite
                result = targetExhausted
                break

            switch (bytesToWrite)   ''' note: everything falls through. '''
            case 4:
                *--target = (UTF8)((ch | byteMark) & byteMask)
                ch >>= 6
            case 3:
                *--target = (UTF8)((ch | byteMark) & byteMask)
                ch >>= 6
            case 2:
                *--target = (UTF8)((ch | byteMark) & byteMask)
                ch >>= 6
            case 1:
                *--target = (UTF8) (ch | firstByteMark[bytesToWrite])

            target += bytesToWrite

        *sourceStart = source
        *targetStart = target
        return result


    ''' --------------------------------------------------------------------- '''

    '''
     * Utility routine to tell whether a sequence of bytes is legal UTF-8.
     * This must be called with the length pre-determined by the first byte.
     * If not calling self from ConvertUTF8to*, the length can be set by:
     length = trailingBytesForUTF8[*source]+1
     * and the sequence is illegal right away if there aren't that many bytes
     * available.
     * If presented with a length > 4, returns False.  The Unicode
     * definition of UTF-8 goes up to 4-byte sequences.
     '''

    static Boolean isLegalUTF8( UTF8 *source, length)
        UTF8 a
         UTF8 *srcptr = source+length
        switch (length)
        default:
            return False
        ''' Everything else falls through when "True"... '''
        case 4:
            if (a = (*--srcptr)) < 0x80 or a > 0xBF:
                return False

        case 3:
            if (a = (*--srcptr)) < 0x80 or a > 0xBF:
                return False

        case 2:
            if (a = (*--srcptr)) < 0x80 or a > 0xBF:
                return False


            switch (*source)
            ''' no fall-through in self inner switch '''
            case 0xE0:
                if a < 0xA0:
                    return False

                break
            case 0xED:
                if a > 0x9F:
                    return False

                break
            case 0xF0:
                if a < 0x90:
                    return False

                break
            case 0xF4:
                if a > 0x8F:
                    return False

                break
            default:
                if a < 0x80:
                    return False



        case 1:
            if *source >= 0x80 and *source < 0xC2:
                return False


        if *source > 0xF4:
            return False

        return True


    ''' --------------------------------------------------------------------- '''

    '''
     * Exported function to return whether a UTF-8 sequence is legal or not.
     * This is not used here; it's just exported.
     '''
    Boolean isLegalUTF8Sequence( UTF8 *source, *sourceEnd)
        length = trailingBytesForUTF8[*source]+1
        if length > sourceEnd - source:
            return False

        return isLegalUTF8(source, length)


    ''' --------------------------------------------------------------------- '''

    static unsigned
    findMaximalSubpartOfIllFormedUTF8Sequence( UTF8 *source,
             UTF8 *sourceEnd)
        UTF8 b1, b2, b3

        assert(not isLegalUTF8Sequence(source, sourceEnd))

        '''
         * Unicode 6.3.0, D93b:
         *
         *   Maximal subpart of an ill-formed subsequence: The longest code unit
         *   subsequence starting at an unconvertible offset that is either:
         *   a. the initial subsequence of a well-formed code unit sequence, or
         *   b. a subsequence of length one.
         '''

        if source == sourceEnd:
            return 0


        '''
         * Perform case analysis.  See Unicode 6.3.0, 3-7. Well-Formed UTF-8
         * Byte Sequences.
         '''

        b1 = *source
        ++source
        if b1 >= 0xC2 and b1 <= 0xDF:
            '''
             * First byte is valid, we know that self code unit sequence is
             * invalid, the maximal subpart has to end after the first byte.
             '''
            return 1


        if source == sourceEnd:
            return 1


        b2 = *source
        ++source

        if b1 == 0xE0:
            return (b2 >= 0xA0 and b2 <= 0xBF) ? 2 : 1

        if b1 >= 0xE1 and b1 <= 0xEC:
            return (b2 >= 0x80 and b2 <= 0xBF) ? 2 : 1

        if b1 == 0xED:
            return (b2 >= 0x80 and b2 <= 0x9F) ? 2 : 1

        if b1 >= 0xEE and b1 <= 0xEF:
            return (b2 >= 0x80 and b2 <= 0xBF) ? 2 : 1

        if b1 == 0xF0:
            if b2 >= 0x90 and b2 <= 0xBF:
                if source == sourceEnd:
                    return 2


                b3 = *source
                return (b3 >= 0x80 and b3 <= 0xBF) ? 3 : 2

            return 1

        if b1 >= 0xF1 and b1 <= 0xF3:
            if b2 >= 0x80 and b2 <= 0xBF:
                if source == sourceEnd:
                    return 2


                b3 = *source
                return (b3 >= 0x80 and b3 <= 0xBF) ? 3 : 2

            return 1

        if b1 == 0xF4:
            if b2 >= 0x80 and b2 <= 0x8F:
                if source == sourceEnd:
                    return 2


                b3 = *source
                return (b3 >= 0x80 and b3 <= 0xBF) ? 3 : 2

            return 1


        assert((b1 >= 0x80 and b1 <= 0xC1) or b1 >= 0xF5)
        '''
         * There are no valid sequences that start with these bytes.  Maximal subpart
         * is defined to have length 1 in these cases.
         '''
        return 1


    ''' --------------------------------------------------------------------- '''

    '''
     * Exported function to return the total number of bytes in a codepoint
     * represented in UTF-8, the value of the first byte.
     '''
    unsigned getNumBytesForUTF8(UTF8 first)
        return trailingBytesForUTF8[first] + 1


    ''' --------------------------------------------------------------------- '''

    '''
     * Exported function to return whether a UTF-8 string is legal or not.
     * This is not used here; it's just exported.
     '''
    Boolean isLegalUTF8String( UTF8 **source, *sourceEnd)
        while (*source != sourceEnd)
            length = trailingBytesForUTF8[**source] + 1
            if length > sourceEnd - *source or not isLegalUTF8(*source, length):
                return False

            *source += length

        return True


    ''' --------------------------------------------------------------------- '''

    ConversionResult ConvertUTF8toUTF16 (
         UTF8** sourceStart, sourceEnd,
        UTF16** targetStart, targetEnd, flags)
        result = conversionOK
         source = *sourceStart
        target = *targetStart
        while (source < sourceEnd)
            ch = 0
            unsigned extraBytesToRead = trailingBytesForUTF8[*source]
            if extraBytesToRead >= sourceEnd - source:
                result = sourceExhausted
                break

            ''' Do self check whether lenient or strict '''
            if not isLegalUTF8(source, extraBytesToRead+1):
                result = sourceIllegal
                break

            '''
             * The cases all fall through. See "Note A" below.
             '''
            switch (extraBytesToRead)
            case 5:
                ch += *source++
                ch <<= 6; ''' remember, UTF-8 '''
            case 4:
                ch += *source++
                ch <<= 6; ''' remember, UTF-8 '''
            case 3:
                ch += *source++
                ch <<= 6
            case 2:
                ch += *source++
                ch <<= 6
            case 1:
                ch += *source++
                ch <<= 6
            case 0:
                ch += *source++

            ch -= offsetsFromUTF8[extraBytesToRead]

            if target >= targetEnd:
                source -= (extraBytesToRead+1); ''' Back up source pointernot  '''
                result = targetExhausted
                break

            if (ch <= UNI_MAX_BMP)   ''' Target is a character <= 0xFFFF '''
                ''' UTF-16 surrogate values are illegal in UTF-32 '''
                if ch >= UNI_SUR_HIGH_START and ch <= UNI_SUR_LOW_END:
                    if flags == strictConversion:
                        source -= (extraBytesToRead+1); ''' return to the illegal value itself '''
                        result = sourceIllegal
                        break

                    else:
                        *target++ = UNI_REPLACEMENT_CHAR


                else:
                    *target++ = (UTF16)ch; ''' normal case '''


            elif ch > UNI_MAX_UTF16:
                if flags == strictConversion:
                    result = sourceIllegal
                    source -= (extraBytesToRead+1); ''' return to the start '''
                    break; ''' Bail out; shouldn't continue '''

                else:
                    *target++ = UNI_REPLACEMENT_CHAR


            else:
                ''' target is a character in range 0xFFFF - 0x10FFFF. '''
                if target + 1 >= targetEnd:
                    source -= (extraBytesToRead+1); ''' Back up source pointernot  '''
                    result = targetExhausted
                    break

                ch -= halfBase
                *target++ = (UTF16)((ch >> halfShift) + UNI_SUR_HIGH_START)
                *target++ = (UTF16)((ch & halfMask) + UNI_SUR_LOW_START)


        *sourceStart = source
        *targetStart = target
        return result


    ''' --------------------------------------------------------------------- '''

    static ConversionResult ConvertUTF8toUTF32Impl(
         UTF8** sourceStart, sourceEnd,
        UTF32** targetStart, targetEnd, flags,
        Boolean InputIsPartial)
        result = conversionOK
         source = *sourceStart
        target = *targetStart
        while (source < sourceEnd)
            ch = 0
            unsigned extraBytesToRead = trailingBytesForUTF8[*source]
            if extraBytesToRead >= sourceEnd - source:
                if flags == strictConversion or InputIsPartial:
                    result = sourceExhausted
                    break

                else:
                    result = sourceIllegal

                    '''
                     * Replace the maximal subpart of ill-formed sequence with
                     * replacement character.
                     '''
                    source += findMaximalSubpartOfIllFormedUTF8Sequence(source,
                              sourceEnd)
                    *target++ = UNI_REPLACEMENT_CHAR
                    continue


            if target >= targetEnd:
                result = targetExhausted
                break


            ''' Do self check whether lenient or strict '''
            if not isLegalUTF8(source, extraBytesToRead+1):
                result = sourceIllegal
                if flags == strictConversion:
                    ''' Abort conversion. '''
                    break

                else:
                    '''
                     * Replace the maximal subpart of ill-formed sequence with
                     * replacement character.
                     '''
                    source += findMaximalSubpartOfIllFormedUTF8Sequence(source,
                              sourceEnd)
                    *target++ = UNI_REPLACEMENT_CHAR
                    continue


            '''
             * The cases all fall through. See "Note A" below.
             '''
            switch (extraBytesToRead)
            case 5:
                ch += *source++
                ch <<= 6
            case 4:
                ch += *source++
                ch <<= 6
            case 3:
                ch += *source++
                ch <<= 6
            case 2:
                ch += *source++
                ch <<= 6
            case 1:
                ch += *source++
                ch <<= 6
            case 0:
                ch += *source++

            ch -= offsetsFromUTF8[extraBytesToRead]

            if ch <= UNI_MAX_LEGAL_UTF32:
                '''
                 * UTF-16 surrogate values are illegal in UTF-32, anything
                 * over Plane 17 (> 0x10FFFF) is illegal.
                 '''
                if ch >= UNI_SUR_HIGH_START and ch <= UNI_SUR_LOW_END:
                    if flags == strictConversion:
                        source -= (extraBytesToRead+1); ''' return to the illegal value itself '''
                        result = sourceIllegal
                        break

                    else:
                        *target++ = UNI_REPLACEMENT_CHAR


                else:
                    *target++ = ch


            else     ''' i.e., ch > UNI_MAX_LEGAL_UTF32 '''
                result = sourceIllegal
                *target++ = UNI_REPLACEMENT_CHAR


        *sourceStart = source
        *targetStart = target
        return result


    ConversionResult ConvertUTF8toUTF32Partial( UTF8 **sourceStart,
             UTF8 *sourceEnd,
            UTF32 **targetStart,
            UTF32 *targetEnd,
            ConversionFlags flags)
        return ConvertUTF8toUTF32Impl(sourceStart, sourceEnd, targetStart, targetEnd,
                                      flags, '''InputIsPartial='''True)


    ConversionResult ConvertUTF8toUTF32( UTF8 **sourceStart,
                                         UTF8 *sourceEnd, **targetStart,
                                        UTF32 *targetEnd, flags)
        return ConvertUTF8toUTF32Impl(sourceStart, sourceEnd, targetStart, targetEnd,
                                      flags, '''InputIsPartial='''False)




''' ---------------------------------------------------------------------

    Note A.
    The fall-through switches in UTF-8 reading code save a
    temp variable, decrements & conditionals.  The switches
    are equivalent to the following loop:
            tmpBytesToRead = extraBytesToRead+1
            do                ch += *source++
                --tmpBytesToRead
                if (tmpBytesToRead) ch <<= 6
            } while (tmpBytesToRead > 0)

    In UTF-8 writing code, switches on "bytesToWrite" are
    similarly unrolled loops.

   --------------------------------------------------------------------- '''
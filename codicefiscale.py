"""
Python library for Italian fiscal code

codicefiscale is a Python library for working with Italian fiscal code numbers
officially known as Italy's Codice Fiscale.

Copyright (C) 2009-2013 Emanuele Rocca
Copyright (C) 2014 Augusto Destrero (support for "Omocodie" [http://it.wikipedia.org/wiki/Omocodia])

Homepage: https://github.com/ema/pycodicefiscale

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""

__version__ = '0.9'
__author__ = "Emanuele Rocca, Augusto Destrero"

import re
# pylint: disable=W0402
import string

__VOWELS = [ 'A', 'E', 'I', 'O', 'U' ]
__CONSONANTS = list(set(list(string.ascii_uppercase)).difference(__VOWELS))

MONTHSCODE = [ 'A', 'B', 'C', 'D', 'E', 'H', 'L', 'M', 'P', 'R', 'S', 'T' ]

# pylint: disable=C0301
_pattern = re.compile("^[A-Z]{6}[0-9LMNPQRSTUV]{2}[ABCDEHLMPRST]{1}[0-9LMNPQRSTUV]{2}[A-Z]{1}[0-9LMNPQRSTUV]{3}[A-Z]{1}$")

def isvalid(code):
    """``isvalid(code) -> bool``

    This function checks if the given fiscal code is valid.

    eg: isvalid('RCCMNL83S18D969H') -> True
        isvalid('RCCMNL83S18D969') -> False
    """
    if not isinstance(code, basestring):
        return False
    if len(code) != 16:
        return False
    code = code.upper()
    if _pattern.match(code) is None:
        return False
    return (control_code(code[0:15]) == code[15])

# Fiscal code calculation 
def __common_triplet(input_string, consonants, vowels):
    """__common_triplet(input_string, consonants, vowels) -> string"""
    output = consonants

    if len(input_string) > 2:
        # likely
        stopat = 3
    else:
        # unlikely (eg: surname = Fo)
        stopat = 2 

    while len(output) < stopat:
        output += vowels.pop(0)
    
    if len(output) == 2:
        output += 'X'

    return output[:3]

def __consonants_and_vowels(input_string):
    """__consonants_and_vowels(input_string) -> (string, list)

    Get the consonants as a string and the vowels as a list.
    """
    input_string = input_string.upper().replace(' ', '')

    consonants = [ char for char in input_string if char in __CONSONANTS ]
    vowels     = [ char for char in input_string if char in __VOWELS ]

    return "".join(consonants), vowels

def __surname_triplet(input_string):
    """__surname_triplet(input_string) -> string"""
    consonants, vowels = __consonants_and_vowels(input_string)

    return __common_triplet(input_string, consonants, vowels)

def __name_triplet(input_string):
    """__name_triplet(input_string) -> string"""
    if input_string == '':
        # highly unlikely: no first name, like for instance some Indian persons
        # with only one name on the passport
        # pylint: disable=W0511
        return 'XXX' 

    consonants, vowels = __consonants_and_vowels(input_string)
    
    if len(consonants) > 3:
        return "%s%s%s" % (consonants[0], consonants[2], consonants[3])

    return __common_triplet(input_string, consonants, vowels)

def control_code(input_string):
    """``control_code(input_string) -> int``

    Computes the control code for the given input_string string. The expected
    input_string is the first 15 characters of a fiscal code.

    eg: control_code('RCCMNL83S18D969') -> 'H'
    """
    assert len(input_string) == 15

    # building conversion tables for even and odd characters positions
    even_controlcode = {}

    for idx, char in enumerate(string.digits):
        even_controlcode[char] = idx

    for idx, char in enumerate(string.ascii_uppercase):
        even_controlcode[char] = idx

    values = [ 1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8,
               12, 14, 16, 10, 22, 25, 24, 23 ]

    odd_controlcode = {}

    for idx, char in enumerate(string.digits):
        odd_controlcode[char] = values[idx]

    for idx, char in enumerate(string.ascii_uppercase):
        odd_controlcode[char] = values[idx]

    # computing the code
    code = 0
    for idx, char in enumerate(input_string):
        if idx % 2 == 0:
            code += odd_controlcode[char]
        else:
            code += even_controlcode[char]
    
    return string.ascii_uppercase[code % 26]

def build(surname, name, birthday, sex, municipality):
    """``build(surname, name, birthday, sex, municipality) -> string``

    Computes the fiscal code for the given person data.

    eg: build('Rocca', 'Emanuele', datetime.datetime(1983, 11, 18), 'M', 'D969') 
        -> RCCMNL83S18D969H
    """

    # RCCMNL
    output = __surname_triplet(surname) + __name_triplet(name)

    # RCCMNL83
    output += str(birthday.year)[2:]

    # RCCMNL83S
    output += MONTHSCODE[birthday.month - 1]

    # RCCMNL83S18
    output += "%02d" % (sex == 'M' and birthday.day or 40 + birthday.day)

    # RCCMNL83S18D969 
    output += municipality

    # RCCMNL83S18D969H
    output += control_code(output)

    assert isvalid(output)

    return output

# info from fiscal code 
def get_birthday(code):
    """``get_birthday(code) -> string``

    Birthday of the person whose fiscal code is 'code', in the format DD-MM-YY. 

    Unfortunately it's not possible to guess the four digit birth year, given
    that the Italian fiscal code uses only the last two digits (1983 -> 83).
    Therefore, this function returns a string and not a datetime object.

    eg: birthday('RCCMNL83S18D969H') -> 18-11-83
    """
    assert isvalid(code)

    day_year_charmap = {}
    for idx, char in enumerate(string.digits):
        day_year_charmap[char] = idx
    for idx, char in enumerate('LMNPQRSTUV'):
        day_year_charmap[char] = idx

    day = day_year_charmap[code[9]] * 10 + day_year_charmap[code[10]]
    day = day < 32 and day or day - 40
    month = MONTHSCODE.index(code[8]) + 1
    year = day_year_charmap[code[6]] * 10 + day_year_charmap[code[7]]

    return "%02d-%02d-%02d" % (day, month, year)

def get_sex(code):
    """``get_sex(code) -> string``

    The sex of the person whose fiscal code is 'code'.

    eg: sex('RCCMNL83S18D969H') -> 'M'
        sex('CNTCHR83T41D969D') -> 'F'
    """
    
    assert isvalid(code)

    return int(code[9:11]) < 32 and 'M' or 'F'

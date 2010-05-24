# A hack to find "haikus" in English text. For the purposes of this program
# a "haiku" is one or more complete sentences that, together, can be broken
# into groups of 5, 7, and 5 syllables. Each canididate haiku line, and then
# the entire haiku, has to make it through a few heuristics to filter out 
# constructions that are likely to scan awkwardly (like verb phrases split
# across lines). Since this code doesn't really try to understand the texts,
# it might throw away a few legitimate phrases, and it certainly lets through
# some bad ones.
#
# Any improvements would be welcomed.
#
# License:
#
# Copyright (c) 2009, Jonathan Feinberg <jdf@pobox.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice, 
#      this list of conditions and the following disclaimer.
#   2. Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#   3. The name of the author may not be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED 
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR 
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from __future__ import with_statement
import nltk
import re
import cPickle as pickle
import gzip
import os.path
import sys

def file(relpath):
    return os.path.join(os.path.dirname(__file__), relpath)

def read_alternates(which):
    with open(file('data/awkward_%s'%which), 'r') as baddies:
        return '|'.join([e.strip() for e in baddies.readlines() if len(e.strip()) > 0])
    
single_line_filters = [
                       re.compile(r'^[a-z][^.?!;:]+([.?!;:]+[^.?!;:]+)+$', re.IGNORECASE),
                       re.compile(r'[.?!;:]+\s+[\'"]?[A-Za-z]+(?:\'[a-z]+)?$'),
                       ]
single_line_filters.append(re.compile(r'^(?:%s)\b'%read_alternates('starts')))
single_line_filters.append(re.compile(r'\b(?:%s)$'%read_alternates('ends'), re.IGNORECASE))
   
first_word_comma = re.compile(r'^\s*[a-z]\w*,')

with open(file('data/awkward_breaks'), 'r') as breaks:
    alts = '|'.join([r'\b%s\b' % ('\n'.join(e.strip().split())) for e in breaks.readlines() if len(e.strip()) > 0]
                    + ['[^\'".?!;:,]\n[a-z]+(?:\'[a-z]+)?[".?!;:]+.',
                       '"\S+\n\S+"',
                       ])
    break_filter = re.compile(alts, re.IGNORECASE)

# load the syllable-count dictionary
with open(file('cmudict/cmudict.pickle'), 'rb') as p:
    syllables = pickle.load(p)
with open(file('cmudict/custom.dict'), 'r') as p:
    for line in p.xreadlines():
        (word, count) = line.split()
        syllables[word] = int(count)

# Use the NLTK to determine sentence boundaries.
sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

number_syllables = (
                #   0  1  2  3  4  5  6  7  8  9
                    2, 1, 1, 1, 1, 1, 1, 2, 1, 1,
                    1, 3, 1, 2, 2, 2, 2, 3, 2, 2,
                    2, 3, 3, 3, 3, 3, 3, 4, 3, 3,
                    2, 3, 3, 3, 3, 3, 3, 4, 3, 3,
                    2, 3, 3, 3, 3, 3, 3, 4, 3, 3,
                    2, 3, 3, 3, 3, 3, 3, 4, 3, 3,
                    2, 3, 3, 3, 3, 3, 3, 4, 3, 3,
                    3, 4, 4, 4, 4, 4, 4, 5, 4, 4,
                    2, 3, 3, 3, 3, 3, 3, 4, 3, 3,
                    2, 3, 3, 3, 3, 3, 3, 4, 3, 3,
                    )
has_digit = re.compile(r'\d')
ordinal = re.compile(r'^(\d\d?)(?:rd|th|st)$', re.IGNORECASE)
too_many_digits = re.compile('\d\d\d')

short_time = re.compile(r'^([1-2]?[0-9])(?:[ap]m)$',re.IGNORECASE)
time = re.compile(r'^([1-2]?[0-9]):(\d\d)([ap]m)?$',re.IGNORECASE)
word_shapes = (
               re.compile(r'^[^a-z0-9\$@]*([-@&_0-9a-z\+]+(?:\'[a-z]+)?)[^a-z0-9]*$', re.IGNORECASE),
               re.compile(r'^[^\$]*(\$\d+(?:\.\d{1,2})?)[^a-z0-9]*$', re.IGNORECASE),
               re.compile(r'^[^a-z0-9]*([1-2]?[0-9]:\d\d(\s*[ap]m)?)[^a-z0-9]*$', re.IGNORECASE),
               )

class Nope(Exception):
    pass

class TooShort(Exception):
    pass

class LineSyllablizer:
    def __init__(self, line, unknown_word_handler=None):
        self.words = line.split()
        self.index = 0
        self.lines = []
        self.unknown_word_handler = unknown_word_handler
    
    def _count_chunk_syllables(self, chunk):
        if has_digit.search(chunk):
            return number_syllables[int(chunk)]
        else:
            return syllables[chunk]
        
    def _count_syllables(self, word, splitter=re.compile(r'(?<=\D)(?=\d)|(?<=\d)(?=\D)')):
        "Raises KeyError, Nope"
        if not word or len(word) == 0:
            return 0
        
        if 'http:' in word:
            raise Nope

        if '0' == word[0] and len(word) > 1:
            return 1 + self._count_syllables(word[1:])  # oh seven
        
        if '$' == word[0]:
            return 2 + self._count_syllables(word[1:]) # 13 dollars
        
        if '@' == word[0]:
            return 1 + self._count_syllables(word[1:]) # user name

        if '&' in word and len(word) > 1:
            return 1 + sum(self._count_syllables(w) for w in word.split('&'))
        
        if '-' in word:
            return sum(self._count_syllables(w) for w in word.split('-'))
        
        if '_' in word:
            return sum(self._count_syllables(w) for w in word.split('_'))
        
        if not has_digit.search(word):
            return syllables[word]
        if too_many_digits.search(word):
            raise Nope
        m = short_time.match(word)
        if m:
            return 2 + number_syllables[int(m.group(1))]
        m = time.match(word)
        if m:
            if m.group(2) == '00':
                minutes = 2
            else:
                minutes = number_syllables[int(m.group(2))]
            partial = number_syllables[int(m.group(1))] + minutes
            if m.group(3):
                return 2 + partial
            return partial
        m = ordinal.match(word)
        if m:
            return number_syllables[int(m.group(1))]
        count = 0
        start = 0
        for m in splitter.finditer(word):
            boundary = m.start()
            count += self._count_chunk_syllables(word[start:boundary])
            start = boundary
        count += self._count_chunk_syllables(word[start:])
        return count
    
    def clean(self, word):
        for shape in word_shapes:
            m = shape.match(word)
            if m:
                return m.group(1).upper()
        return None

    def count_syllables(self):
        si = 0
        syllable_count = 0
        try:
            for word in self.words:
                syllable_count += self._count_syllables(self.clean(word))
        except KeyError:
            print "I don't know '%s'"%word
            return -1
        except Nope:
            print "I can't do '%s'"%word
            return -1
        return syllable_count
    
    def seek(self, n):
        si = self.index
        syllable_count = 0
        try:
            while syllable_count < n:
                word = self.clean(self.words[self.index])
                syllable_count += self._count_syllables(word)
                self.index += 1
        except KeyError:
            if word and self.unknown_word_handler:
                self.unknown_word_handler(word)
            raise Nope
        except IndexError:
            raise TooShort
        if syllable_count > n:
            raise Nope
        line = ' '.join(self.words[si:self.index])
        for f in single_line_filters:
            if f.search(line):
                raise Nope
        self.lines.append(line)
    
    def seek_eol(self):
        if self.index != len(self.words):
            raise Nope

    def bad_split(self, n):
        return awkward_in_front_without_punct_before.search(self.lines[n]) and not self.lines[n - 1][-1] in (',', ';', '-')
        
    def find_haiku(self):
        self.seek(5)
        self.seek(7)
        self.seek(5)
        self.seek_eol()
        if first_word_comma.search(self.lines[1]) or first_word_comma.search(self.lines[2]):
            raise Nope
        if break_filter.search('\n'.join(self.lines)):
            raise Nope
        return self.lines
        

class HaikuFinder:
    def __init__(self, text, unknown_word_handler=None):
        self.lines = sentence_tokenizer.tokenize(text)
        self.unknown_word_handler = unknown_word_handler
        
    def find_haikus(self):
        haikus = []
        line_index = 0
        line_count = len(self.lines)
        while line_index < line_count:
            offset = 0
            line = ""
            while line_index + offset < line_count:
                line = "%s %s" % (line, self.lines[line_index + offset])
                try:
                    haikus.append(LineSyllablizer(line, self.unknown_word_handler).find_haiku())
                    break
                except Nope:
                    break
                except TooShort:
                    offset += 1
            line_index += 1
        return haikus
    
    @classmethod
    def add_word(cls, word, syllable_count):
        syllables[word.upper()] = syllable_count

def find_haikus(text,  unknown_word_handler=None):
    return HaikuFinder(text, unknown_word_handler).find_haikus()

def count_syllables(text):
    return LineSyllablizer(text).count_syllables()


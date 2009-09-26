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

single_line_filters = (
                       re.compile(r'^[a-z][^.?!;:]+([.?!;:]+[^.?!;:]+)+$'),
                       re.compile(r'^[a-z]\w+[\'"]?[.?!;:]'),
                       re.compile(r'[.?!;:]+\s+\w+(\'\w+)?$'),
                       re.compile(r'''
                            \b
                            (?:
                                a|the|an|he|she|I|
                                we|they|as|of|and|
                                with|my|your|to|so|
                                which|that|it|for|
                                have|in|at|this|his|her|
                                you|\w+'s|than|they're|
                                we're|s?he's|i'm|you're|
                                its|if
                            )
                            $
                            ''', re.IGNORECASE | re.VERBOSE),
                       re.compile(r'^(?:him|her|me|us|them|of|you is)\b', re.IGNORECASE),
                       )

awkward_in_front_without_punct_before = re.compile(r'^(?:its?|an?|they)\b')
first_word_comma = re.compile(r'^\s*\w+,')

# load the syllable-count dictionary
with open(os.path.join(os.path.dirname(__file__), 'cmudict/cmudict.pickle'), 'rb') as p:
    syllables = pickle.load(p)
with open(os.path.join(os.path.dirname(__file__), 'cmudict/custom.dict'), 'r') as p:
    for line in p.xreadlines():
        (word, count) = line.split()
        syllables[word] = int(count)

# Use the NLTK to determine sentence boundaries.
sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

class Nope(Exception):
    pass

class TooShort(Exception):
    pass

class LineSyllablizer:
    def __init__(self, line, unknown_word_handler):
        self.words = line.split()
        self.index = 0
        self.lines = []
        self.unknown_word_handler = unknown_word_handler
        
    def clean(self, word, wp=re.compile(r'^[^a-z]*([a-z\+]+(?:\'[a-z]+)?)[^a-z]*$', re.IGNORECASE)):
        m = wp.match(word)
        if not m:
            return None
        return m.group(1).upper()
    
    def seek(self, n):
        si = self.index
        syllable_count = 0
        try:
            while syllable_count < n:
                word = self.clean(self.words[self.index])
                syllable_count += syllables[word]
                self.index += 1
        except KeyError:
            if word:
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
        if self.bad_split(1) or self.bad_split(2):
            raise Nope
        if first_word_comma.search(self.lines[1]) or first_word_comma.search(self.lines[2]):
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

#! /bin/env python

from __future__ import with_statement
import nltk
import re
import cPickle as pickle
import gzip
import os.path

half_sentence = re.compile(r'^[a-z][^.?!;:]+([.?!;:]+[^.?!;:]+)+$')
one_word_start = re.compile(r'^[a-z]\w+[\'"]?[.?!;:]')
one_word_end = re.compile(r'[.?!;:]+\s+\w+(\'\w+)?$')
bad_end = re.compile(r'''
    \b        # any of the following words
    (?:
        a|the|an|he|she|I|we|they|as|of|and|with|my|your|to|so
    )
    $        # at the end
    ''', re.IGNORECASE | re.VERBOSE)
awkward_in_front = re.compile(r'^(?:him|me|us|them|of|you is)\b', re.IGNORECASE)

with open(os.path.join(os.path.dirname(__file__),'cmudict.pickle'),'rb') as p:
    syllables = pickle.load(p)
sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

class Nope(Exception):
    pass

class TooShort(Exception):
    pass

class LineSyllablizer:
    def __init__(self,line):
        self.words = line.split()
        self.index = 0
        self.lines = []
        
    def clean(self, word, wp = re.compile(r'^[^a-z]*([a-z]+(?:\'[a-z]+)?)[^a-z]*$', re.IGNORECASE)):
        m = wp.match(word)
        if not m:
            return None
        return m.group(1).upper()
    
    def seek(self, n):
        si = self.index
        syllable_count = 0
        try:
            while syllable_count < n:
                syllable_count += syllables[self.clean(self.words[self.index])]
                self.index += 1
        except KeyError:
            raise Nope
        except IndexError:
            raise TooShort
        if syllable_count > n:
            raise Nope
        line = ' '.join(self.words[si:self.index])
        if awkward_in_front.search(line):
            raise Nope
        if one_word_start.search(line):
            raise Nope
        if one_word_end.search(line):
            raise Nope
        if bad_end.search(line):
            raise Nope
        if half_sentence.search(line):
            raise Nope
        self.lines.append(line)
    
    def seek_eol(self):
        if self.index != len(self.words):
            raise Nope

    def find_haiku(self):
        self.seek(5)
        self.seek(7)
        self.seek(5)
        self.seek_eol()
        return self.lines
        

class HaikuFinder:
    def __init__(self, text):
        self.lines = sentence_tokenizer.tokenize(text)
        
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
                    haikus.append(LineSyllablizer(line).find_haiku())
                    break
                except Nope:
                    break
                except TooShort:
                    offset += 1
            line_index += 1
        return haikus

if __name__ == '__main__':
    import sys
    try:
        t = sys.argv[1]
    except:
        t = 'debug.txt'
    with open(t, "r") as text:
        for haiku in HaikuFinder(text.read()).find_haikus():
            print haiku[0]
            print "    %s"%haiku[1]
            print haiku[2]
            print



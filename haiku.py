#! /bin/env python

import sys
import nltk
import re

text = open(sys.argv[1],'r').read()

syllables = dict()
force_valid = re.compile(r'[.?!"\']$')
invalid_sentence = re.compile(r'[.?!;:]+\s*.')

for line in file('cmudict.0.7a'):
    (word, sp, phonemes) = line.partition(' ')
    if '(' in word:
        continue
    count = len([x for x in list(phonemes) if x >= '0' and x <= '9'])
    syllables[word] = count

class Nope(Exception):
    pass

class Syllablizer:
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
            raise Nope
        if syllable_count > n:
            raise Nope
        line = ' '.join(self.words[si:self.index])
        if invalid_sentence.search(line) and not force_valid.search(line):
            raise Nope
        self.lines.append(line)
    
    def find_haiku(self):
        self.seek(5)
        self.seek(7)
        self.seek(5)
        self.eol()
        
    def eol(self):
        if self.index != len(self.words):
            raise Nope

    def dump(self, stream):
        stream.write("%s\n"%self.lines[0])
        stream.write("    %s\n"%self.lines[1])
        stream.write("%s\n\n"%self.lines[2])
        

sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

for line in sentence_tokenizer.tokenize(text):
    syl = Syllablizer(line)
    try:
        syl.find_haiku()
        syl.dump(sys.stdout)
    except Nope:
        continue

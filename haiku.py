#! /bin/env python

import sys
import nltk
import re

#text = open(sys.argv[1],'r').read()

syllables = dict()
bad_end = re.compile(r'[.?!;:]+\s*.|\b(?:a|the|an|he|she|I|we|they|as|of|and|with|my|your)$', re.IGNORECASE)
ok_end = re.compile(r'[.?!"\']$')
object_in_front = re.compile(r'^(?:him|me|us|them)\b', re.IGNORECASE)

parenned = re.compile(r'\(\d+\)')
for line in file('cmudict.0.7a'):
    (word, sp, phonemes) = line.partition(' ')
    if '(' in word:
        word = parenned.sub('',word)
    count = len([x for x in list(phonemes) if x >= '0' and x <= '9'])
    if syllables.has_key(word):
        count = min(count, syllables[word])
    syllables[word] = count

class Nope(Exception):
    pass

class TooShort(Exception):
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
            raise TooShort
        if syllable_count > n:
            raise Nope
        line = ' '.join(self.words[si:self.index])
        if object_in_front.search(line):
            raise Nope
        if bad_end.search(line) and not ok_end.search(line):
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
        
def syllablize(line, out):
    syl = Syllablizer(line)
    try:
        syl.find_haiku()
        syl.dump(out)
    except Nope:
        pass

sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')


import cherrypy
import cStringIO

class HaikuSite:

    @cherrypy.expose
    def index(self):
        # Ask for the user's name.
        return '''
            <form action="findhaikus" method="POST">
            Enter some text here:<br>
            <input type="submit" /><br>
            <textarea rows="40" cols="80" name="text"></textarea>
            </form>'''
    
    @cherrypy.expose
    def findhaikus(self, text = None):
        if text:
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            out = cStringIO.StringIO()
            lines = sentence_tokenizer.tokenize(text)
            line_index = 0
            line_count = len(lines)
            while line_index < line_count:
                line = lines[line_index]
                offset = 0
                while True:
                    try:
                        syllablize(line, out)
                    except TooShort:
                        offset += 1
                        if line_index + offset >= line_count:
                            break
                        line = "%s %s" % (line, lines[line_index + offset])
                    break
                line_index += 1
            haikus = out.getvalue()
            out.close()
            return haikus
        else:
            cherrypy.response.headers['Location'] = '/'
            cherrypy.response.status = 302

cherrypy.tree.mount(HaikuSite())

if __name__ == '__main__':
    import os.path
    thisdir = os.path.dirname(__file__)
    cherrypy.quickstart(config=os.path.join(thisdir, 'haiku.conf'))

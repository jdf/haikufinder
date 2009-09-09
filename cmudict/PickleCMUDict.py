import cPickle as pickle
import re
syllables = dict()
parenned = re.compile(r'\(\d+\)')
for line in file('cmudict.0.7a'):
    (word, sp, phonemes) = line.partition(' ')
    if '(' in word:
        word = parenned.sub('',word)
    count = len([x for x in list(phonemes) if x >= '0' and x <= '9'])
    if syllables.has_key(word):
        count = min(count, syllables[word])
    syllables[word] = count
output = open('cmudict.pickle', 'wb')
pickle.dump(syllables, output, pickle.HIGHEST_PROTOCOL)
output.close()
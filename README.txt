Installer: http://MrFeinberg.com/haikufinder-1.0.zip

* 
*	REQUIRES NLTK, THE NATURAL LANGUAGE TOOLKIT
*	http://www.nltk.org/download
*

A Python hack to find "haikus" in English text. For the purposes of this
module, a "haiku" is one or more complete sentences that, together, can be
broken into groups of 5, 7, and 5 syllables. Each canididate haiku line, 
and then the entire haiku, has to make it through a few heuristics to 
filter out constructions that are likely to scan awkwardly (like verb 
phrases split across lines). Since this code doesn't really try to 
understand the texts, it might throw away a few legitimate phrases, and it 
certainly lets through some bad ones.

Any improvements would be welcomed.

The license, found in license.txt, is "modified BSD".

Example usage:

	text = open("ulysses.txt", "r").read()
	haikus = HaikuFinder(text).find_haikus()
	for haiku in haikus:
	    print haiku[0]
	    print "    %s" % haiku[1]
	    print haiku[2]
	    print

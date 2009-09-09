from __future__ import with_statement
from haiku import HaikuFinder
from mako.template import Template
import cherrypy
import cStringIO
import sys

class HaikuSite:
    def __init__(self):
        with open("templates/index.html", "r") as t:
            self.template = Template(t.read())
            
    @cherrypy.expose
    def index(self, text=None):
        if text:
            haikus = HaikuFinder(text).find_haikus()
            if haikus:
                return self.template.render_unicode(haikus=haikus).encode('utf-8', 'replace')
            else:
                return self.template.render_unicode(nonefound=True).encode('utf-8', 'replace')
        return self.template.render_unicode().encode('utf-8', 'replace')

if __name__ == '__main__':
    import os.path
    thisdir = os.path.dirname(__file__)
    cherrypy.quickstart(HaikuSite(), config=os.path.join(thisdir, 'haiku.conf'))

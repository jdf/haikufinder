from __future__ import with_statement
from haiku import HaikuFinder
from mako.template import Template
import cherrypy
import cStringIO
import sys
import os.path

thisdir = os.path.dirname(__file__)

class HaikuSite:
    def __init__(self):
        with open(os.path.join(thisdir, "templates/index.html"), "r") as t:
            self.template = Template(t.read())
            
    @cherrypy.expose
    def haikufinder(self, text=None):
        if text:
            haikus = HaikuFinder(text).find_haikus()
            if haikus:
                return self.template.render_unicode(haikus=haikus).encode('utf-8', 'replace')
            else:
                return self.template.render_unicode(nonefound=True).encode('utf-8', 'replace')
        return self.template.render_unicode().encode('utf-8', 'replace')

if __name__ == '__main__':
    import os.path
    cherrypy.config.update({'environment': 'production',
                            'log.error_file': 'haiku.log'})
    cherrypy.quickstart(HaikuSite(), config=os.path.join(thisdir, 'haiku.conf'))

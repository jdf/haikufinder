from __future__ import with_statement
from haiku import HaikuFinder
from mako.template import Template
import web
import os.path
import re

thisdir = os.path.dirname(os.path.abspath(__file__))
templates = os.path.join(thisdir, "templates")
static = os.path.join(thisdir, "static")

class HaikuFindingPage:
    def __init__(self, content_type, template):
        with open(os.path.join(templates, template), "r") as t:
            self.content_type = content_type
            self.template = Template(t.read())
    
    def decorate(self, s):
        web.header('Content-Length', len(s))
        return s
    
    def GET(self):
        web.header('Content-Type', self.content_type)
        return self.decorate(self.template.render_unicode().encode('utf-8', 'replace'))
    
    def POST(self):
        haikus = HaikuFinder(web.input().text).find_haikus()
        web.header('Content-Type', self.content_type)
        if haikus:
            return self.decorate(self.template.render_unicode(haikus=haikus).encode('utf-8', 'replace'))
        else:
            return self.decorate(self.template.render_unicode(nonefound=True).encode('utf-8', 'replace'))

class HTMLPage(HaikuFindingPage):
    def __init__(self):
        HaikuFindingPage.__init__(self, "text/html", "index.html")
        
class TextPage(HaikuFindingPage):
    def __init__(self):
        HaikuFindingPage.__init__(self, "text/plain", "text.plain")

types = { 
         'css': 'text/css',
         'js': 'text/javascript',
        }

class Resource:
    def __init__(self):
        self.cache = dict()
        
    def ct(self, resource):
        try:
            return types[resource.split(".")[-1].lower()]
        except:
            return "application/octet-stream"

    def GET(self, resource):
        if not self.cache.has_key(resource):
            if resource in os.listdir(static):
                ct = self.ct(resource)
                web.header("Content-Type", ct)
                with open(os.path.join(static,resource),"rb") as f:
                    r = f.read()
                self.cache[resource] = (ct,r)
            else:
                self.cache[resource] = None
                
        r = self.cache[resource]
        if r is None:
            return web.notfound()
        else:
            web.header("Content-Type", r[0])
            return r[1]

if __name__ == '__main__':
    urls = (
            r'/haikufinder/static/(.*)', Resource,            
            r'/haikufinder/text/?', TextPage,
            r'/haikufinder/?', HTMLPage,
            r'/text/?', TextPage,
            r'/static/(.*)', Resource,
            r'/', HTMLPage,
            )
    web.config.debug = False
    app = web.application(urls, globals())
    app.run()
    
    

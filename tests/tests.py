import httplib
import mockhttp
import os.path
import unittest2
import urllib

ROOT = os.path.dirname(__file__)

def p(*parts):
    return os.path.join(ROOT, *parts)

class UrllibTestCase(unittest2.TestCase):
    def test_patching(self):
        with mockhttp.patch('urllib', (
                # no params is default
                (('http://foo.bar.com',), p('fixtures', 'sample.html')),
                (('http://foo.bar.com', 'GET'), p('fixtures', 'sample.html')),
                (('http://foo.bar.com', 'GET', {'a': 'b'}), p('fixtures', 'sample.html')),
                (('http://foo.bar.com', 'POST', {'a': 'b'}), p('fixtures', 'sample.html')),
                (('http://foo.bar.com', 'POST', {'a': 'b'}), mockhttp.response(status=404, headers=())),
            )):

            resp = urllib.urlopen('http://foo.bar.com/')
            self.assertEquals(resp.read(), '<strong>hello!</strong>')

            # TODO: this should raise a 404 error
            # resp = urllib.urlopen('http://foo.bar.com/baz', 'a=b')
            # print repr(resp.read())

class HttplibCase(unittest2.TestCase):
    def test_patching(self):
        with mockhttp.patch('httplib', (
                # no params is default
                (('http://foo.bar.com',), p('fixtures', 'sample.html')),
                (('http://foo.bar.com', 'GET'), p('fixtures', 'sample.html')),
                (('http://foo.bar.com', 'GET', {'a': 'b'}), p('fixtures', 'sample.html')),
                (('http://foo.bar.com', 'POST', {'a': 'b'}), p('fixtures', 'sample.html')),
                (('http://foo.bar.com', 'POST', {'a': 'b'}), mockhttp.response(status=404, headers=())),
            )):

            conn = httplib.HTTPConnection('foo.bar.com')
            conn.request('GET', '/')
            
            resp = conn.getresponse()
            self.assertEquals(resp.read(), '<strong>hello!</strong>')

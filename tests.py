import unittest2
import urllib
import mockhttp

class UrllibTestCase(unittest2.TestCase):
    def test_patching(self):
        with mockhttp.patch('urllib', (
                # no params is default
                (('http://foo.bar.com',), 'path/to/file.json'),
                (('http://foo.bar.com', 'GET'), 'path/to/file.json'),
                (('http://foo.bar.com', 'GET', {'a': 'b'}), 'path/to/file.json'),
                (('http://foo.bar.com', 'POST', {'a': 'b'}), 'path/to/file.json'),
                (('http://foo.bar.com', 'POST', {'a': 'b'}), mockhttp.response(status=404, headers=())),
            )):
            r = urllib.urlopen('http://foo.bar.com', 'a=b')
            # TODO: this should raise a 404 error
            print r.read()

**Work in progress** library to mock http requests and return predefined fixtures for their results.

Will support at least urllib, urllib2, and httplib (in the basic forms).

::

    with mockhttp.patch('urllib', (
            # no params is default
            (('http://foo.bar.com',), 'path/to/file.json'),
            (('http://foo.bar.com', 'GET'), 'path/to/file.json'),
            (('http://foo.bar.com', 'GET', {'a': 'b'}), 'path/to/file.json'),
            (('http://foo.bar.com', 'POST', {'a': 'b'}), 'path/to/file.json'),
            (('http://foo.bar.com', 'POST', {'a': 'b'}), mockhttp.response(status=404, headers=())),
        )):
        
        r = urllib.urlopen('http://foo.bar.com', 'a=b')
        print r.read()
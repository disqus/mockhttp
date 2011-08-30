mockhttp
========

**Work in progress** library to mock http requests and return predefined fixtures for their results.

Whats Done
----------

* basic urllib support (only tested with urlopen, non SSL)
* basic httplib support (only with non SSL)

Usage
-----

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

TODO
----

* coverage :)
* https suport
* urllib2

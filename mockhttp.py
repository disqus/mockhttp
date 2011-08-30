import hashlib
import mock
from collections import defaultdict
from functools import wraps
from urlparse import urlparse, parse_qs

__all__ = ('patch', 'response')

class MockResponse(object):
    def __init__(self, fixture=None, status=200, headers=()):
        self.fixture = fixture
        self.status = status
        self.headers = headers

    def read(self):
        if not self.fixture:
            return ''
        return open(self.fixture, 'rb').read()

response = MockResponse

def _make_response(f):
    if isinstance(f, MockResponse):
        return f
    return MockResponse(f)

class MockRequest(object):
    def __init__(self, url=None, method=None, params={}):
        if method:
            method = method.upper()

        self.url = url
        self.method = method
        self.params = params

        self.sig = _make_signature(url, method, params)

def _make_request(*args):
    if isinstance(args[0], MockRequest):
        assert len(args) == 1
        return args[0]
    return MockRequest(*args)

def _make_signature(url=None, method=None, params={}):
    if not url:
        return ()
    if not method:
        return (url,)
    if not params:
        return (url, method)

    params_hash = hashlib.md5()
    for key, values in sorted(params.iteritems()):
        if not isinstance(values, (list, tuple)):
            values = [values]
        for value in values:
            params_hash.update('%s=%s&' % (key, value))

    return (url, method, params_hash.hexdigest())

def _tup_pref_matches(t1, t2):
    n = 0
    for i, x in enumerate(t1):
        try:
            if t1[i] == t2[i]:
                i += 1
            else:
                break
        except IndexError:
            break
    return n

class MockHandler(object):
    def __init__(self, mock_obj, fixtures):
        self.mock_obj = mock_obj
        self.fixtures = fixtures

    def _get_response_fixture(self, url, method, params):
        this_signature = _make_signature(url, method, params)
        best = tuple()
        for request, response in self.fixtures:
            matches = _tup_pref_matches(request.sig, this_signature)
            if not matches or len(best) >= matches:
                continue
            best = signature
        if best:
            return best
        return MockResponse(status=404)

class MockUrlOpen(MockHandler):
    def read(self):
        kwargs = defaultdict(lambda:None)
        named_args = ['url', 'data', 'proxies']
        call_args = self.mock_obj.call_args
        for i, x in enumerate(call_args[0]):
            kwargs[named_args[i]] = x
        kwargs.update(self.mock_obj.call_args[1])

        if kwargs['data']:
            method = 'POST'
        else:
            method = 'GET'
        
        if kwargs['data']:
            params = parse_qs(kwargs['data'])
        else:
            params = {}
        
        parsed = urlparse(kwargs['url'])
        if parsed.query:
            for k, v in parse_qs(parsed.query).iteritems():
                if k not in params:
                    params[k] = v
                else:
                    params[k].extend(v)

        match = self._get_response_fixture(kwargs['url'], method, params)

        if match.fixture:
            body = open(match.fixture, 'rb').read()
        else:
            body = ''
        return body

class MockHttpConnection(MockHandler):
    pass

class PatchContextManager(object):
    """
    with mockhttp.patch('urllib', (
            # no params is default
            (('http://foo.bar.com',), 'path/to/file.json'),
            (('http://foo.bar.com', 'GET'), 'path/to/file.json'),
            (('http://foo.bar.com', 'GET', {'a': 'b'}), 'path/to/file.json'),
            (('http://foo.bar.com', 'POST', {'a': 'b'}), 'path/to/file.json'),
            (('http://foo.bar.com', 'POST', {'a': 'b'}), mockhttp.response(status=404, headers=())),
        )):
    """
    def __init__(self, libname, fixtures=()):
        assert libname in ('urllib', 'urllib2', 'httplib.HTTPConnection', 'httplib.HTTPSConnection')
        self.libname = libname
        self.fixtures = [(_make_request(k), _make_response(v)) for k, v in fixtures]
        self._cm = None

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return inner

    def __enter__(self):
        if self.libname in ('urllib', 'urllib2'):
            libpath = '%s.urlopen' % self.libname
            mock_cls = MockUrlOpen
        else:
            libpath = self.libname
            mock_cls = MockHttpConnection
        
        self._patcher = mock.patch(libpath)
        mock_obj = self._patcher.start()
        mock_obj.return_value = mock_cls(mock_obj, self.fixtures)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._patcher.stop()

patch = PatchContextManager
import hashlib
import httplib
import mock
from functools import wraps
from StringIO import StringIO
from urlparse import urlparse, parse_qs

__all__ = ('patch', 'response')

class MockResponse(object):
    def __init__(self, fixture=None, status=200, headers=(), version='HTTP/1.1'):
        self.fixture = fixture
        self.status = status
        self.headers = headers
        self.version = version
        if self.fixture:
            self.fp = open(self.fixture, 'rb')
        else:
            self.fp = StringIO()

    def read(self):
        return self.fp.read()

    def readline(self):
        return self.fp.readline()

response = MockResponse

def _make_response(f):
    if isinstance(f, MockResponse):
        return f
    return MockResponse(f)

class MockRequest(object):
    def __init__(self, url=None, method=None, params={}):
        if method:
            method = method.upper()

        # Ensure we end with a valid path
        if url and url.count('/') == 2:
            url += '/'

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

    # Ensure we end with a valid path
    if url.count('/') == 2:
        url += '/'

    if not method:
        return (url,)
    
    method = method.upper()
    
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
                n += 1
            else:
                break
        except IndexError:
            break
    return n

def _get_response_fixture(fixtures, url, method, params):
    this_signature = _make_signature(url, method, params)
    best_num = 0
    best_resp = None
    
    for request, response in fixtures:
        matches = _tup_pref_matches(request.sig, this_signature)
        if not matches or best_num >= matches:
            continue
        best_num = matches
        best_resp = response
    if best_resp:
        return best_resp
    return MockResponse(status=404)

def make_response_class(response, parent):
    class new(parent):
        def __init__(self, sock, debuglevel=0, strict=0, method=None, buffering=False):
            self.debuglevel = debuglevel
            self.strict = strict
            self._method = method

            self.msg = None

            # from the Status-Line of the response
            self.version = httplib._UNKNOWN # HTTP-Version
            self.status = httplib._UNKNOWN  # Status-Code
            self.reason = httplib._UNKNOWN  # Reason-Phrase

            self.chunked = httplib._UNKNOWN         # is "chunked" being used?
            self.chunk_left = httplib._UNKNOWN      # bytes left to read in current chunk
            self.length = httplib._UNKNOWN          # number of bytes left in response
            self.will_close = httplib._UNKNOWN      # conn will close at end of response
            self.fp = None

        def begin(self):
            self.status = response.status
            if response.version == 'HTTP/1.0':
                self.version = 10
            elif response.version.startswith('HTTP/1.'):
                self.version = 11   # use HTTP/1.1 code for HTTP/1.x where x>=1
            elif response.version == 'HTTP/0.9':
                self.version = 9
            else:
                raise httplib.UnknownProtocol(response.version)
            
            self.will_close = 1
            self.fp = response
            
        def read(self):
            return response.read()
        
    new.__name__ = parent.__name__
    return new

def make_send_wrapper(fixtures):
    """
    This is for urllib support, and is ugly as shit.
    """
    s = []
    def send(self, data):
        last = None
        split_data = data.split('\r\n')
        for lineno, line in enumerate(split_data):
            if lineno == 0:
                path, version = line.split(' ')[1:]
            elif not last:
                break
            lineno += 1
            last = line

        url = 'http://%s' % self.host
        if self.port != 80:
            url += ':%s' % self.port
        url += path
        body = '\n'.join(split_data[lineno:])

        if body:
            params = parse_qs(body)
        else:
            params = {}

        parsed = urlparse(url)
        if parsed.query:
            for k, v in parse_qs(parsed.query).iteritems():
                if k not in params:
                    params[k] = v
                else:
                    params[k].extend(v)

        response = _get_response_fixture(fixtures, url, self._method, params)

        self.__state = httplib._CS_REQ_SENT
        
        if not s:
            s.append(self.response_class)

        self.response_class = make_response_class(response, s[0])
    return send

def make_send_request_wrapper(fixtures):
    s = []
    def _send_request(self, method, path, body=None, headers={}):
        global response_class
        
        """Send a complete request to the server."""
        if body:
            params = parse_qs(body)
        else:
            params = {}

        parsed = urlparse(path)
        if parsed.query:
            for k, v in parse_qs(parsed.query).iteritems():
                if k not in params:
                    params[k] = v
                else:
                    params[k].extend(v)

        url = 'http://%s' % self.host
        if self.port != 80:
            url += ':%s' % self.port
        url += path

        response = _get_response_fixture(fixtures, url, method, params)

        self._method = method
        setattr(self, '_%s__state' % self.__class__.__name__, httplib._CS_REQ_SENT)
        
        if not s:
            s.append(self.response_class)

        self.response_class = make_response_class(response, s[0])
    return _send_request

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
        assert libname in ('urllib', 'urllib2', 'httplib')
        self.libname = libname
        self.fixtures = [(_make_request(*k), _make_response(v)) for k, v in fixtures]
        self._cm = None

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return inner

    def __enter__(self):
        self._patchers = [
            mock.patch.object(httplib.HTTPConnection, 'send', make_send_wrapper(self.fixtures)),
            mock.patch.object(httplib.HTTPConnection, '_send_request', make_send_request_wrapper(self.fixtures)),
        ]
        for patcher in self._patchers:
            patcher.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in self._patchers:
            patcher.stop()

patch = PatchContextManager
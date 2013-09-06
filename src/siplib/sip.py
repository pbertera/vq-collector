#!/usr/bin/python
# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-

import cStringIO


class SipError(Exception):
    pass


class SipUnpackError(SipError):
    pass


class SipNeedData(SipUnpackError):
    pass


class SipPackError(SipError):
    pass


def canon_header(s):
    exception = {'call-id': 'Call-ID', 'cseq':
                 'CSeq', 'www-authenticate': 'WWW-Authenticate'}
    short = ['allow-events', 'u', 'call-id', 'i', 'contact', 'm',
             'content-encoding', 'e', 'content-length', 'l',
             'content-type', 'c', 'event', 'o', 'from', 'f',
             'subject', 's', 'supported', 'k', 'to', 't', 'via', 'v']
    s = s.lower()
    return ((len(s) == 1) and s in short and canon_header(short[short.index(s) - 1])) \
        or (s in exception and exception[s]) or '-'.join([x.capitalize() for x in s.split('-')])


def parse_headers(f):
    """Return dict of HTTP headers parsed from a file object."""
    d = {}
    while 1:
        line = f.readline()
        line = line.strip()
        if not line:
            break
        l = line.split(None, 1)
        if not l[0].endswith(':'):
            raise SipUnpackError('invalid header: %r' % line)
        k = l[0][:-1].lower()
        d[k] = len(l) != 1 and l[1] or ''
    return d


def parse_body(f, headers):
    """Return SIP body parsed from a file object, given HTTP header dict."""
    if 'content-length' in headers:
        n = int(headers['content-length'])
        body = f.read(n)
        if len(body) != n:
            raise SipNeedData(
                'short body (missing %d bytes)' % (n - len(body)))
    elif 'content-type' in headers:
        body = f.read()
    else:
        body = ''
    return body


class Message:

    """SIP Protocol headers + body."""
    __metaclass__ = type
    __hdr_defaults__ = {}
    headers = None
    body = None

    def __init__(self, *args, **kwargs):
        if args:
            self.unpack(args[0])
        else:
            self.headers = {}
            self.body = ''
            for k, v in self.__hdr_defaults__.iteritems():
                setattr(self, k, v)
            for k, v in kwargs.iteritems():
                setattr(self, k, v)

    def unpack(self, buf):
        f = cStringIO.StringIO(buf)
        # Parse headers
        self.headers = parse_headers(f)
        # Parse body
        self.body = parse_body(f, self.headers)
                # Save the rest
        self.data = f.read()

    def pack_hdr(self):
        return ''.join(['%s: %s\r\n' % (canon_header(k), v) for k, v in self.headers.iteritems()])

    def __len__(self):
        return len(str(self))

    def __str__(self):
        return '%s\r\n%s' % (self.pack_hdr(), self.body)


class Request(Message):

    """SIP request."""
    __hdr_defaults__ = {
        'method': 'INVITE',
        'uri': 'sip:user@example.com',
        'version': '2.0',
        'headers': {'to': '', 'from': '', 'call-id': '', 'cseq': '', 'contact': ''}
    }
    __methods = dict.fromkeys((
                              'ACK', 'BYE', 'CANCEL', 'INFO', 'INVITE', 'MESSAGE', 'NOTIFY',
                              'OPTIONS', 'PRACK', 'PUBLISH', 'REFER', 'REGISTER', 'SUBSCRIBE',
                              'UPDATE'
                              ))
    __proto = 'SIP'

    def unpack(self, buf):
        f = cStringIO.StringIO(buf)
        line = f.readline()
        l = line.strip().split()
        if len(l) != 3 or l[0] not in self.__methods or \
                not l[2].startswith(self.__proto):
            raise SipUnpackError('invalid request: %r' % line)
        self.method = l[0]
        self.uri = l[1]
        self.version = l[2][len(self.__proto) + 1:]
        Message.unpack(self, f.read())

    def __str__(self):
        return '%s %s %s/%s\r\n' % (self.method, self.uri, self.__proto,
                                    self.version) + Message.__str__(self)


class Response(Message):

    """SIP response."""
    __hdr_defaults__ = {
        'version': '2.0',
        'status': '200',
        'reason': 'OK',
        'headers': {'to': '', 'from': '', 'call-id': '', 'cseq': '', 'contact': ''}
    }
    __proto = 'SIP'

    def unpack(self, buf):
        f = cStringIO.StringIO(buf)
        line = f.readline()
        l = line.strip().split(None, 2)
        if len(l) < 2 or not l[0].startswith(self.__proto) or not l[1].isdigit():
            raise SipUnpackError('invalid response: %r' % line)
        self.version = l[0][len(self.__proto) + 1:]
        self.status = l[1]
        self.reason = l[2]
        Message.unpack(self, f.read())

    def __str__(self):
        return '%s/%s %s %s\r\n' % (self.__proto, self.version, self.status,
                                    self.reason) + Message.__str__(self)

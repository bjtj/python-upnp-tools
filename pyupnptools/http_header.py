import os
from collections import OrderedDict
import re
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class FirstLine:
    def __init__(self, line):
        if line:
            self._tokens = re.split(r' |\t', line, maxsplit=2)

    def __getitem__(self, idx):
        return self._tokens[idx]

    def __str__(self):
        return ' '.join(self._tokens)


class HttpHeader:
    def __init__(self, firstline=None, headers=OrderedDict()):
        self._firstline = FirstLine(firstline)
        self._headers = headers

    def firstline(self, line=None):
        if not line:
            return self._firstline
        self._firstline = FirstLine(line)

    @staticmethod
    def read(text):
        header = HttpHeader()
        lines = text.splitlines()
        header.firstline(lines[0])
        for line in lines[1:]:
            if not line:
                break
            tokens = line.split(':', 1)
            key = tokens[0].strip()
            value = tokens[1].strip()
            header[key] = value
        return header

    def clear(self):
        self._headers = OrderedDict()
        
    def __getitem__(self, key):
        return self._headers[key.upper()][1]

    def __setitem__(self, key, value):
        self._headers[key.upper()] = (key, value)

    def __str__(self):
        firstline = self._firstline
        fields = '\r\n'.join(['{}: {}'.format(v[0], v[1]) for v in self._headers.values()])
        return '{}\r\n{}\r\n'.format(firstline, fields)


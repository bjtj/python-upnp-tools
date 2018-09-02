import os
import socket
import select
import time
from .http_header import *
import logging
import traceback
from . import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class NotifyType:

    ALIVE = "ssdp:alive"
    BYEBYE = "ssdp:byebye"
    UPDATE = "ssdp:update"
    
    def __init__(self, str_repr):
        self._str_repr = str_repr
        if NotifyType.ALIVE == str_repr:
            return
        if NotifyType.BYEBYE == str_repr:
            return
        if NotifyType.UPDATE == str_repr:
            return
        raise Exception('Unknown notify type -- {}'.format(str_repr))

    def __eq__(self, other):
        if type(other) == type(''):
            return self._str_repr == other
        return self._str_repr == other._str_repr

    def __str__(self):
        return self._str_repr


class SSDP:
    mcast_host = "239.255.255.250"
    mcast_port = 1900
    def __init__(self):
        raise Exception("Not Allowed")


class SsdpHeader(HttpHeader):
    def __init__(self, header):
        self.__dict__ = header.__dict__

    def is_notify(self):
        return self._firstline[0].upper() == 'NOTIFY'

    def is_msearch(self):
        return self._firstline[0].upper() == 'M-SEARCH'

    def is_http_response(self):
        return self._firstline[0].upper().startswith('HTTP')

    def get_notify_type(self):
        return NotifyType(self.__getitem__('NTS'))

    def get_usn(self):
        return self.__getitem__('USN')

    def get_location(self):
        return self.__getitem__('LOCATION')
    


class SsdpListener:
    def __init__(self):
        self._finishing = False
        self._handler = None

    def finish(self):
        self._finishing = True

    def register(self, handler):
        self._handler = handler

    def _handle_ssdp(self, ssdp_header):
        if self._handler:
            self._handler(ssdp_header)

    def run(self):
        self._finishing = False
        _sock = socket.socket(socket.AF_INET,
                               socket.SOCK_DGRAM,
                               socket.IPPROTO_UDP)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sock.bind(('0', SSDP.mcast_port))

        inputs = [_sock]
        outputs = []
        
        while not self._finishing:
            _timeout = 1
            readables, writables, exceptionals = select.select(inputs,
                                                              outputs,
                                                              inputs,
                                                              _timeout)

            for readable in readables:
                packet = _sock.recv(4096)
                try:
                    ssdp_header = HttpHeader.read(packet.decode('utf-8'))
                    self._handle_ssdp(SsdpHeader(ssdp_header))
                except Exception as e:
                    traceback.print_exc()
                    logger.debug(e)

        _sock.close()

    def finish(self):
        self._finishing = True
        
        


def send_msearch(st, mx=3, user_agent='UPnP/x App/x Python/x', ext={}):
    header = HttpHeader("M-SEARCH * HTTP/1.1")
    header["HOST"] = "{}:{}".format(SSDP.mcast_host, SSDP.mcast_port)
    header["MAN"] = '"ssdp:discover"'
    header["MX"] = str(mx)
    header["ST"] = st
    header["USER-AGENT"] = user_agent
    for k in ext.keys():
        header[k] = ext[k]
    packet = str(header)

    need_write = True
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.setblocking(0)

    start = time.time()

    inputs = [sock]
    outputs = [sock]

    response_list = []
    while (time.time() - start) < mx:
        _timeout = 1
        readable, writable, _ = select.select(inputs, outputs, inputs, _timeout)
        for _sock in readable:
            data = _sock.recv(4096)
            ssdp_header = HttpHeader.read(data.decode('utf-8'))
            response_list.append(SsdpHeader(ssdp_header))
        for _sock in writable:
            if need_write:
                _sock.sendto(packet.encode(), (SSDP.mcast_host, SSDP.mcast_port))
                start = time.time()
                need_write = False

    return response_list

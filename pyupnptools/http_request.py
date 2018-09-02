from .upnp import *
import requests
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class HttpRequest(UPnPRequest):
    def __init__(self, url):
        self._url = url
        
    def request(self, method='GET', *args, **kwargs):
        try:
            res = getattr(requests, method.lower())(self._url, *args, **kwargs)
        except AttributeError:
            res = requests.request(method.lower(), self._url, *args, **kwargs)
        logger.debug('http response / status code: {}'.format(res.status_code))
        ret = UPnPResponse()
        for k in res.headers.keys():
            ret.header(k, res.headers[k])
        ret.data(res.text.encode('utf-8'))
        return ret
        

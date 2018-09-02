from .upnp import *
from .upnp_url import *
from .upnp_soap import *
from .http_request import *


class UPnPActionInvoke:

    def __init__(self, device, service, action, params):
        self._device = device
        self._service = service
        self._action = action
        self._params = params

    def _get_request(self, url):
        return HttpRequest(url)

    
    def invoke(self):
        url = urljoin(self._device.base_url, self._service.controlUrl())
        soap_req = UPnPSoapRequest(self._service.serviceType(),
                                   self._action.name,
                                   self._params)
        req = self._get_request(url)
        headers = {
            'Content-Type': 'application/xml',
            'SOAPACTION': '"{}#{}"'.format(self._service.serviceType(),
                                           self._action.name)
        }
        logger.debug(soap_req)
        res = req.request(method="post", data=str(soap_req), headers=headers)
        soap_res = UPnPSoapResponse.read(res.data())
        logger.debug(soap_res)
        return soap_res

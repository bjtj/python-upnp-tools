from .upnp import *
from .http_server import *
import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UPnPServiceProperty(OrderedDict):
    def __init__(self, service):
        self.service = service


class UPnPDeviceSession:
    def __init__(self, device):
        self._active = False
        self.device = device
        self.device.renew_expire()
        self._action_request_handlers = None
        self._property_change_listener = None
        self._service_properties = {service.serviceType(): UPnPServiceProperty(service)
                                    for service in device.all_services()}

    def set_active(self, active):
        self._active = active

    def is_active(self):
        return self._active

    def get_device_description(self):
        pass

    def get_scpd(self):
        pass

    def notify_alive(self):
        pass

    def notify_byebye(self):
        pass

    def set_action_request_handler(self, handler):
        self._action_request_handler = handler

    def on_action_request(self, action, params):
        out_params = {}
        if self._action_request_handler:
            out_params = self._action_request_handler(action, params)
        return out_params

    def set_property(self, service_type, name, value):
        props = self._service_properties[service_type]
        props[name] = value
        self.on_property_set(name, value)

    def set_property_change_listener(self, listener):
        self._property_change_listener = listener

    def on_property_set(self, name, value):
        if self._property_change_listener:
            self._property_change_listener(name, value)


class UPnPServer:

    def __init__(self, port=0):
        self._finishing = False
        self._device_sessions = {}
        self._ssdp_listener = None
        self._http_server = HttpServer(port)
        self._interval = 10
        self._ssdp_listener_thread = None
        self._http_server_thread = None
        self._interval_task_thread = None

    def register_device(self, device):
        session = UPnPDeviceSession(device)
        self._device_sessions[device.udn()] = session
        return session

    def unregister_device(self, device):
        del self._device_sessions[device.udn()]

    def _notify_alive(self):
        logger.debug('notify alive')

    def _interval_task(self):
        self._notify_alive()

    def _loop_interval_task(self):
        _start = time.time()
        while not self._finishing:
            if time.time() - _start > self._interval:
                self._interval_task()
                _start = time.time()

    def _resolve_ssdp(self, ssdp_header):
        if ssdp_header.is_msearch():
            # todo:
            pass

    def _run_ssdp_listener(self):
        self._ssdp_listener = SsdpListener()
        self._ssdp_listener.register(self._resolve_ssdp)
        self._ssdp_listener.run()

    def start(self):
        pass

    def finish(self):
        pass

    


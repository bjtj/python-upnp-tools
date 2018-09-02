from .upnp import *
from .upnp_action_invoke import *
from .http_request import *
from .upnp_event_sub import *
from .upnp_url import *
import logging
import threading


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UPnPControlPoint:
    def __init__(self, port = 0):
        logger.debug('upnp control point')
        self._finishing = False
        self._running = False
        self._devices = {}
        self._device_listeners = set()
        self._event_listeners = set()
        self._ssdp_listener = None
        self._http_server = HttpServer(port)
        def _request_handler(method, path, text):
            if method == 'NOTIFY':
                notify = UPnPEventNotify.read(text)
                logger.debug(notify)
        self._http_server.register(_request_handler)
        self._subscriptions = {}
        self._ssdp_listener_thread = None
        self._http_server_thread = None
        self._interval_job_thread = None
        self._interval = 10

    def finishing(self):
        return self._finishing

    def is_running(self):
        return self._running

    def clear_devices(self):
        udns = [x for x in self._devices.keys()]
        for udn in udns:
            self._remove_device(self._devices[udn])

    def send_msearch(self, *args, **kwargs):
        lst = ssdp.send_msearch(*args, **kwargs)
        for item in lst:
            self._resolve_ssdp(item)

    def invoke(self, device, service, action, params):
        invoker = UPnPActionInvoke(device, service, action, params)
        return invoker.invoke()

    def subscribe(self, device, service):
        server_addr = self._http_server.get_server_address()
        cb_path = '/event'
        url = urljoin(device.base_url, service.eventSubURL())
        headers = {
            'NT': 'upnp:event',
            'CALLBACK': '<http://{}:{}{}>'.format(server_addr[0],
                                                  server_addr[1],
                                                  cb_path),
            'TIMEOUT': 'Second-1800'
        }
        req = self._get_request(url)
        res = req.request(method = 'SUBSCRIBE', headers = headers)
        sid = res.header('SID')
        timeout = int(res.header('TIMEOUT').split('-')[-1])
        logger.debug('subscription sid: {} / timeout: {}'.format(sid, timeout))
        self._subscriptions[sid] = UPnPSubscription(device, service, sid, timeout)
        return sid

    def renew_subscription(self, subscription):
        url = urljoin(subscription.device.base_url,
                      subscription.service.eventSubURL())
        headers = {
            'SID': subscription.sid,
            'TIMEOUT': 'Second-1800'
        }
        req = self._get_request(url)
        res = req.request(method='SUBSCRIBE', headers=headers)
        subscription.renew_expire()

    def unsubscribe(self, subscription):
        url = urljoin(subscription.device.base_url,
                      subscription.service.eventSubURL())
        req = self._get_request(url)
        headers = {
            'SID': subscription.sid
        }
        req.request(method = 'UNSUBSCRIBE', headers = headers)

    def get_subscription(self, sid):
        return self._subscriptions[sid]

    def register_device_listener(self, listener):
        self._device_listeners.add(listener)

    def unregister_device_listener(self, listener):
        self._device_listeners.remove(listener)

    def register_event_listener(self, listener):
        self._event_listeners.add(listener)

    def unregister_event_listener(self, listener):
        self._event_listeners.remove(listener)

    def _get_device(self, udn):
        if udn in self._devices:
            return self._devices[udn]
        return None

    def _get_request(self, url):
        return HttpRequest(url)

    def _build_device(self, ssdp_header):
        base_url = ssdp_header.get_location()
        req = self._get_request(base_url)
        res = req.request()
        device = UPnPDevice.read(res.data())
        device.base_url = base_url
        for service in device.services:
            scpdurl = urljoin(base_url, service.scpdUrl())
            service.scpd = self._build_scpd(scpdurl)
        return device

    def _build_scpd(self, scpdurl):
        req = self._get_request(scpdurl)
        res = req.request()
        return UPnPScpd.read(res.data())

    def _add_device(self, device):
        udn = device.udn()
        self._devices[udn] = device
        for listener in self._device_listeners:
            listener.on_device_added(device)

    def _resolve_add_device(self, ssdp_header):
        device = self._get_device(USN.read(ssdp_header.get_usn()).udn())
        if device:
            device.renew_expire()
        else:
            self._add_device(self._build_device(ssdp_header))

    def _remove_device(self, device):
        udn = device.udn()
        if udn in self._devices:
            for listener in self._device_listeners:
                listener.on_device_removed(self._devices[udn])
            del self._devices[udn]

    def on_event(self, event):
        for event_listener in self._event_listeners:
            event_listener.on_event(event)

    def _run_ssdp_listener(self):
        logger.debug('run ssdp listener')
        self._ssdp_listener = SsdpListener()
        self._ssdp_listener.register(self._resolve_ssdp)
        self._ssdp_listener.run()

    def _resolve_ssdp(self, ssdp_header):
        if ssdp_header.is_notify():
            nt = ssdp_header.get_notify_type()
            if nt == NotifyType.ALIVE:
                self._resolve_add_device(ssdp_header)
            elif nt == NotifyType.BYEBYE:
                device = self._get_device(USN.read(ssdp_header.get_usn()).udn())
                if device:
                    self._remove_device(device)
            elif nt == NotifyType.UPDATE:
                device = self._get_device(USN.read(ssdp_header.get_usn()).udn())
                if device:
                    device.renew_expire()
        elif ssdp_header.is_msearch():
            # ignore
            pass
        elif ssdp_header.is_http_response():
            self._resolve_add_device(ssdp_header)

    def _resolve_expired_devices(self):
        expires = [device for device in self._devices.values() if device.is_expired()]
        for expired in expires:
            self._remove_device(expired)

    def _resolve_expired_subscriptions(self):
        sids = [subscription.sid for subscription in self._subscriptions.values()
                if subscription.is_expired()]
        for sid in sids:
            del self._subscriptions[sid]

    def _renew_subscriptions(self):
        for subscription in self._subscriptions.values():
            self.renew_subscription(subscription)

    def _loop_interval_job(self):
        _start = time.time()
        while not self._finishing:
            if time.time() - _start > self._interval:
                self._on_interval_job()
                _start = time.time()

    def _on_interval_job(self):
        logger.debug('interval task')
        self._resolve_expired_devices()
        self._renew_subscriptions()
        # self._resolve_expired_subscriptions() -- need it?

    def _run_thread(self, *args, **kwargs):
        th = threading.Thread(*args, **kwargs)
        th.daemon = True
        th.start()
        return th
        
    def start(self):

        if self._running:
            raise Exception('Already in running')
        
        logger.debug('start')
        
        self._running = True
        self._interval_job_thread = self._run_thread(target=self._loop_interval_job)
        self._ssdp_listener_thread = self._run_thread(target=self._run_ssdp_listener)
        self._http_server_thread = self._run_thread(target=self._http_server.run)

    def stop(self):

        self._finishing = True

        self._ssdp_listener.finish()
        self._http_server.finish()

        if self._interval_job_thread:
            self._interval_job_thread.join()

        if self._ssdp_listener_thread:
            self._ssdp_listener_thread.join()

        if self._http_server_thread:
            self._http_server_thread.join()

        self._running = False
            


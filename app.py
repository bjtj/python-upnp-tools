from pyupnptools import SSDP, SsdpListener, NotifyType, send_msearch, UPnPControlPoint, UPnPDevice, UPnPDeviceListener, UPnPScpd, HttpServer, UPnPSoapRequest, UPnPSoapResponse
import time
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(name)s %(levelname).1s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def print_device(device):
    print('[{}]'.format(device))
    for service in device.services:
        print(' - {}'.format(service))
        scpd = service.scpd
        for action in scpd.actions:
            print('  * {}()'.format(action))
            for argument in action.arguments:
                print('   - [{}] {}'.format(argument.direction, argument.name))


def handle_ssdp(ssdp_header):
    if ssdp_header.is_notify():
        if ssdp_header.get_notify_type() == NotifyType.ALIVE:
            print('Location: {}'.format(ssdp_header.get_location()))

def start_ssdp_listener():
    listener = SsdpListener()
    listener.register(handle_ssdp)
    listener.run()

def start_send_msearch():
    lst = send_msearch('ssdp:all', mx=3)
    for item in lst:
        print(item)

def build_device():
    with open('device.xml', 'r') as f:
        xml = f.read()
        device = UPnPDevice.read(xml)
        for service in device.services:
            with open('scpd.xml', 'r') as fout:
                service.scpd = UPnPScpd.read(fout.read())

        print_device(device)


def build_scpd():
    with open('scpd.xml', 'r') as f:
        xml = f.read()
        scpd = UPnPScpd.read(xml)


class Any:
    pass


def start_control_point():

    __scope = Any()
    __scope.sid = None
    
    class Listener(UPnPDeviceListener):
        def __init__(self, shared_scope):
            self.shared_scope = shared_scope
            
        def on_device_added(self, device):
            print("Added: '{}'".format(device.friendlyName()))
            print_device(device)
            if device['deviceType'] == 'urn:schemas-upnp-org:device:DimmableLight:1':
                service = device.get_service(
                    'urn:schemas-upnp-org:service:SwitchPower:1')
                action = service.scpd.get_action('GetTarget')
                params = {}
                ret = cp.invoke(device, service, action, params)
                print('Action invoke result: {}'.format(ret))
            self.shared_scope.sid = cp.subscribe(device, service)
            print('Subscribe / sid: {}'.format(self.shared_scope.sid))

        def on_device_removed(self, device):
            print("Removed: '{}'".format(device.friendlyName()))

    cp = UPnPControlPoint()
    cp.register_device_listener(Listener(__scope))
    print('Start')
    cp.start()
    print('Send msearch')
    cp.send_msearch('ssdp:all')


    print('Sleep 60 seconds...')
    time.sleep(60)

    if __scope.sid:
        print('Unsubscribe')
        cp.unsubscribe(cp.get_subscription(__scope.sid))
    
    print('Stop')
    cp.stop()
    print('Clear devices')
    cp.clear_devices()
    

def run_http_server():
    server = HttpServer(0)
    addr = server.get_server_address()
    print('Server address: {}'.format(addr))
    server.run()

def build_soap_request():
    with open('action_request.xml', 'r') as f:
        service_type = 'urn:schemas-upnp-org:service:ContentDirectory:1'
        action_name = 'GetSystemUpdateID'
        req = UPnPSoapRequest.read(service_type, action_name, f.read())
        print(req)


def build_soap_response():
    with open('action_response.xml', 'r') as f:
        res = UPnPSoapResponse.read(f.read())
        print(res)
    
            
def main():
    # start_send_msearch()
    # build_device()
    start_control_point()
    # build_scpd()
    # run_http_server()
    # build_soap_request()
    # build_soap_response()

if __name__ == '__main__':
    main()


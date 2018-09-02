from . import *
import logging
from .upnp_xml import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class UPnPSubscription:
    def __init__(self, device, service, sid, timeout):
        self.device = device
        self.service = service
        self.sid = sid
        self.timeout = timeout
        self._register_time = time.time()

    def renew_expire(self):
        self._register_time = time.time()

    def is_expired(self):
        return time.time() - self._register_time > self.timeout

class UPnPEventListener:
    def on_event(self, event):
        pass
    

class UPnPEventNotify(OrderedDict):

    def __str__(self):
        from io import BytesIO
        import xml.etree.ElementTree as ET
        ns_table = {
            'e': 'urn:schemas-upnp-org:event-1-0'
        }
        for k,v in ns_table.items():
            ET.register_namespace(k, v)

        propertyset = ET.Element('{{{}}}propertyset'.format(ns_table['e']))
        for k, v in self.items():
            prop = ET.SubElement(propertyset, '{{{}}}property'.format(ns_table['e']))
            elem = ET.SubElement(prop, k)
            elem.text = v
        et = ET.ElementTree(propertyset)
        f = BytesIO()
        et.write(f, encoding='utf-8', xml_declaration=True)
        xml = f.getvalue().decode('utf-8')
        return xml
    
    @staticmethod
    def read(text):
        notify = UPnPEventNotify()
        root = read_xml(text)
        for child in root:
            if get_tagname(child) == 'property':
                for prop_node in child:
                    if not list(prop_node):
                        name = get_tagname(prop_node)
                        value = prop_node.text
                        notify[name] = value

        return notify

        

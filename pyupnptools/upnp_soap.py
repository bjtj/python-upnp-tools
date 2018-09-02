from .upnp import *
from .upnp_xml import *
from collections import OrderedDict


class UPnPSoapRequest(OrderedDict):

    def __init__(self, service_type, action_name, params=None):
        super(UPnPSoapRequest, self).__init__()
        self.service_type = service_type
        self.action_name = action_name
        if params:
            self.update(params)

    def __str__(self):
        from io import BytesIO
        import xml.etree.ElementTree as ET
        ns_table = {
            's': 'http://schemas.xmlsoap.org/soap/envelope/',
            'u': self.service_type
        }
        for k,v in ns_table.items():
            ET.register_namespace(k, v)

        envelope = ET.Element('{{{}}}Envelope'.format(ns_table['s']))
        body = ET.SubElement(envelope, '{{{}}}Body'.format(ns_table['s']))
        action = ET.SubElement(body, '{{{}}}{}'.format(ns_table['u'],
                                                       self.action_name))
        for k, v in self.items():
            elem = ET.SubElement(action, k)
            elem.text = v
        et = ET.ElementTree(envelope)
        f = BytesIO()
        et.write(f, encoding='utf-8', xml_declaration=True)
        xml = f.getvalue().decode('utf-8')
        return xml
    
    @staticmethod
    def read(service_type, action_name, text):
        req = UPnPSoapRequest(service_type, action_name)
        root = read_xml(text)
        for child in root:
            if get_tagname(child) == 'Body':
                for action_node in child:
                    # get_tagname(action_node) == action_name
                    for prop_node in action_node:
                        if not list(prop_node):
                            name = get_tagname(prop_node)
                            value = prop_node.text
                            req[name] = value

        return req


class UPnPSoapResponse(OrderedDict):

    def __init__(self):
        super(UPnPSoapResponse, self).__init__()

    def __str__(self):
        from io import BytesIO
        import xml.etree.ElementTree as ET
        ns_table = {
            's': 'http://schemas.xmlsoap.org/soap/envelope/',
            'u': self.service_type
        }
        for k,v in ns_table.items():
            ET.register_namespace(k, v)

        envelope = ET.Element('{{{}}}Envelope'.format(ns_table['s']))
        body = ET.SubElement(envelope, '{{{}}}Body'.format(ns_table['s']))
        action = ET.SubElement(body, '{{{}}}{}Response'.format(ns_table['u'],
                                                               self.action_name))
        for k, v in self.items():
            elem = ET.SubElement(action, k)
            elem.text = v
        et = ET.ElementTree(envelope)
        f = BytesIO()
        et.write(f, encoding='utf-8', xml_declaration=True)
        xml = f.getvalue().decode('utf-8')
        return xml
    
    @staticmethod
    def read(text):
        res = UPnPSoapResponse()
        root = read_xml(text)
        for node in root:
            if get_tagname(node) == 'Body':
                for action_node in node:
                    res.service_type = get_namespace(action_node)
                    response_action_name = get_tagname(action_node)
                    res.action_name = response_action_name[:-len('Response')]
                    for prop_node in action_node:
                        if not list(prop_node):
                            name = get_tagname(prop_node)
                            value = prop_node.text
                            res[name] = value
        return res




import time
from collections import OrderedDict
from .upnp_xml import *

class _UPnPModel(OrderedDict):
    def __getitem__(self, key):
        return super(_UPnPModel, self).__getitem__(key.upper())[1]

    def __setitem__(self, key, value):
        super(_UPnPModel, self).__setitem__(key.upper(), (key, value))


class UPnPDevice(_UPnPModel):
    def __init__(self):
        super(UPnPDevice, self).__init__()
        self._register_time = time.time()
        self._expire_time = time.time() + 1800
        self.children = []
        self.services = []
        self.base_url = ''

    def renew_expire(self):
        self._register_time = time.time()

    def is_expired(self):
        return time.time() >= self._expire_time

    def udn(self):
        return self.__getitem__('udn')

    def friendlyName(self):
        return self.__getitem__('friendlyName')

    def get_service(self, st):
        for service in self.services:
            if service.serviceType() == st:
                return service
        return None

    def __str__(self):
        return '{} / {}'.format(self.udn(), self.friendlyName())
    
    @staticmethod
    def read(data):
        logger.debug(data)
        root = read_xml(data)
        for child in root:
            if child.tag.endswith('device'):
                return UPnPDevice.read_xml_node(child)
        raise Exception('No device node found')

    @staticmethod
    def read_xml_node(device_node):
        device = UPnPDevice()
        embedded_devices = []
        for child in device_node:
            tagname = get_tagname(child)
            
            if tagname == 'deviceList':
                device.children = [UPnPDevice.read_xml_node(device_node)
                                   for device_node in child
                                   if get_tagname(device_node) == 'device']
            elif tagname == 'serviceList':
                device.services = [UPnPService.read_xml_node(service_node)
                                   for service_node in child
                                   if get_tagname(service_node) == 'service']
            elif not list(child):
                value = child.text
                device[tagname] = value
        
        return device
                
class UPnPService(_UPnPModel):

    def __init__(self):
        super(UPnPService, self).__init__()
        self.scpd = None

    def serviceType(self):
        return self.__getitem__('serviceType')

    def serviceId(self):
        return self.__getitem__('serviceid')
    
    def scpdUrl(self):
        return self.__getitem__('SCPDURL')

    def controlUrl(self):
        return self.__getitem__('controlURL')

    def eventSubURL(self):
        return self.__getitem__('eventSubURL')

    def __str__(self):
        return '{} / {}'.format(self.serviceId(), self.serviceType())
    
    @staticmethod
    def read_xml_node(node):
        service = UPnPService()
        for child in node:
            if not list(child):
                name = get_tagname(child)
                value = child.text
                service[name] = value
        return service


class UPnPAction(_UPnPModel):
    def __init__(self):
        self.name = ''
        self.arguments = []

    def __str__(self):
        return self.name
    
    @staticmethod
    def read_xml_node(node):
        action = UPnPAction()
        for child in node:
            if get_tagname(child) == 'name':
                action.name = child.text
            elif get_tagname(child) == 'argumentList':
                action.arguments = [UPnPActionArgument.read_xml_node(argument_node)
                                    for argument_node in child
                                    if get_tagname(argument_node) == 'argument']

        return action


class UPnPActionArgument(_UPnPModel):
    def __init__(self):
        self.name = ''
        self.direction = ''
        self.stateVariableName = ''

    def __str__(self):
        return self.name
    
    @staticmethod
    def read_xml_node(node):
        argument = UPnPActionArgument()
        for child in node:
            if get_tagname(child) == 'name':
                argument.name = child.text
            elif get_tagname(child) == 'direction':
                argument.direction = child.text
            elif get_tagname(child) == 'relatedStateVariable':
                argument.stateVariableName = child.text

        return argument


class UPnPStateVariable(_UPnPModel):
    def __init__(self):
        self.name = ''
        self.dataType = ''

    def __str__(self):
        return ''
    
    @staticmethod
    def read_xml_node(node):
        state_variable = UPnPStateVariable()
        for child in node:
            if get_tagname(child) == 'name':
                state_variable.name = child.text
            elif get_tagname(child) == 'dataType':
                state_variable.dataType = child.text
        return state_variable

    
class UPnPScpd(_UPnPModel):
    def __init__(self):
        self.actions = []
        self.state_variables = []

    def __str__(self):
        return ''

    def get_action(self, action_name):
        for action in self.actions:
            if action.name == action_name:
                return action
        return None
    
    @staticmethod
    def read(xml):
        root = read_xml(xml)
        scpd = UPnPScpd()
        for node in root:
            tagname = get_tagname(node)
            if tagname == 'specVersion':
                pass
            elif tagname == 'actionList':
                scpd.actions = [UPnPAction.read_xml_node(action_node) for action_node
                                in node if get_tagname(action_node) == 'action']
            elif tagname == 'serviceStateTable':
                scpd.state_variables = [UPnPStateVariable.read_xml_node(state_variable_node)
                                        for state_variable_node in node
                                        if get_tagname(state_variable_node) == 'stateVariable']
                    
        return scpd

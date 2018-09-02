import xml.etree.ElementTree as ET
import re
from . import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def read_xml(text):
    return ET.fromstring(text)

def get_namespace(node):
    return re.match(r'{(.+)}', node.tag).group(1)
    
def get_tagname(node):
    return node.tag.split('}')[-1]

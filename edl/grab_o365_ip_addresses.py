# Parse XML from MS website with O365 IP ranges, convert into PAN EDL format

import json
import math
import urllib2
import ssl
import xml.etree.ElementTree as ET

f = open('/var/nginx/html/iprange/o365_ips.list','w')
html = urllib2.urlopen('http://support.content.office.net/en-us/static/O365IPAddresses.xml')

output = html.read()

root = ET.fromstring(output)

for ip_type in root.getiterator('addresslist'):
    if ip_type.attrib['type'] == 'IPv4':
        for ip_addr in ip_type:
            f.write(ip_addr.text + "\n")
    elif ip_type.attrib['type'] == 'IPv6':
        for ip_addr in ip_type:
            f.write(ip_addr.text + "\n")

f.close()

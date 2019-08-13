"""
Parse data (ip addresses) from a page on wiki
"""

import urllib.request
import base64
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

download_url='https://wiki.domain.com/display/ITIOTOOLS/Domain+Controllers+list'
username=''
password=''
out_file_path='parse-wiki-page.txt'

req = urllib.request.Request(download_url)

credentials = ('%s:%s' % (username, password))
encoded_credentials = base64.b64encode(credentials.encode('ascii'))
req.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))

with urllib.request.urlopen(req,context=ctx) as response, open(out_file_path, 'w') as out_file:
    data = response.read().decode('utf-8')
    ip=re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:\/\d{1,2})?',str(data))
    out_file.write('\n'.join(set(ip)))

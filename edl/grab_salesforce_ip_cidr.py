# sf website uses ajax so the rendered webpage data is cannot be found in the page source
# need to pass additional headers to extract the required info
# hopefully some day they will publish this in txt/json format like AWS does

import urllib.request
import re

req_data=b'{"action":"Help_HomeController","method":"getArticleData","data":[{"urlName":"000003652","language":"en_US","type":"KBKnowledgeArticle"}],"type":"rpc","tid":5,"ctx":{"csrf":"VmpFPSxNakF4T0Mwd09DMHlOVlF5TXpvek1EbzBNeTQxTnpGYSxqNWR5eWdLa05JSWYxRUpaZWhsWk5CLE9EVTFZVFJs","vid":"06630000001hrjK","ns":"","ver":35}}'

req=urllib.request.Request('https://help.salesforce.com/apexremote',data=req_data)
req.add_header('Content-Type','application/json')
req.add_header('Referer','https://help.salesforce.com/articleView?id=000003652&type=1')

with urllib.request.urlopen(req) as r:
        res=r.read().decode('utf-8')

ip=re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:\/\d{1,2})',str(res))

with open('ip-ranges-sf.txt','w') as f:
        f.write('\n'.join(set(ip)))

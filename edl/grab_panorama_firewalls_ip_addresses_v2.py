# Get list of firewalls from panorama, connect to each via API, obtain NAT addresses from rules

import pan.xapi
import xml.etree.ElementTree as ET
import ipaddress
import pprint
import sys

key=""
hostname="panorama.domain.com"

xapi = pan.xapi.PanXapi(api_key=key,hostname=hostname)

xapi.op(cmd='show devices connected',cmd_xml=True)

root_panorama = ET.fromstring(xapi.xml_result())

firewalls_number = len(root_panorama.findall('entry'))



def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

fw_num_counter = 0

output={} # nested dictionary populated with output

for firewall in root_panorama.iter(tag='entry'):

    fw_interface_no_address=False
    
    if firewall.find('serial') is not None:
        fw_serial = firewall.find('serial').text
        fw_hostname = firewall.find('hostname').text

        progress(fw_num_counter,firewalls_number,fw_hostname)
    
        fw_num_counter += 1
        
        output[fw_hostname]={}
        output[fw_hostname]["serial"]=fw_serial
        output[fw_hostname]["interfaces"]={}

        xapi_fw = pan.xapi.PanXapi(api_key=key,hostname=hostname,serial=fw_serial)

        xapi_fw.op(cmd='show interface "management"',cmd_xml=True)
        fw_interfaces = ET.fromstring('<root>'+xapi_fw.xml_result()+'</root>') #adding <root> node to fix broken XML
        for fw_interface in fw_interfaces.findall('info'):

                    try:
                        fw_int_ip = ipaddress.ip_interface(fw_interface.find('ip').text)
                    
                    except Exception as exception:
                        fw_int_ip=ipaddress.ip_interface('0.0.0.0/0') # Normalizing exceptions with N/A addresses
                        fw_interface_no_address=True
                    
                    fw_interface_name=fw_interface.find('name').text
                    
                    if (not fw_interface_no_address) and (not fw_int_ip.is_link_local):
                        output[fw_hostname]["interfaces"][fw_interface_name]={}
                    
                    # if address is private start checking NAT table

                    if ( fw_int_ip.is_private ) and ( not fw_int_ip.is_link_local ) and ( not fw_int_ip.ip.compressed == '0.0.0.0' ): 

                        output[fw_hostname]["interfaces"][fw_interface_name]={}
                        output[fw_hostname]["interfaces"][fw_interface_name]["private_ip_address"]=str(fw_int_ip.exploded)
                        #get PAT rule name for this address via eth1/1    
                        try: 
                            
                            no_nat_rule1=False
                            cmd='test nat-policy-match protocol "6" source "' + fw_int_ip.ip.compressed + '" from "LAN-CORP" to "UNTRUST-L3" destination "8.8.8.8" to-interface "ethernet1/1" destination-port "80"'
                            xapi_fw.op(cmd,cmd_xml=True)
                            
                            fw_nat_rule_name1 = ET.fromstring('<root>' + xapi_fw.xml_result() + '</root>')
                            
                            nat_rule1=fw_nat_rule_name1[0][0].text
                            output[fw_hostname]["nat_rule_1"]=[]
                        
                        except Exception as exception:
                            no_nat_rule1=True
                            output[fw_hostname]["nat_rule"]="No NAT rule associated"
                        #get PAT rule name for this address via eth1/2
                         
                        try: 
                            no_nat_rule2=False
                            xapi_fw.op(cmd='test nat-policy-match protocol "6" source "' + fw_int_ip.ip.compressed + '" from "LAN-CORP" to "UNTRUST-L3" destination "8.8.8.8" to-interface "ethernet1/2" destination-port "80"',cmd_xml=True)
                            fw_nat_rule_name2 = ET.fromstring('<root>' + xapi_fw.xml_result() + '</root>')

                            nat_rule2=fw_nat_rule_name2[0][0].text
                            output[fw_hostname]["nat_rule_2"]=[]

                        except Exception as exception:
                            no_nat_rule2=True
                            output[fw_hostname]["nat_rule"]="No NAT rule associated"
                            
                        # collect running config for this rule, to parse <translated-address> entry
                        if not no_nat_rule1:
                            
                            xapi_fw.show(xpath="/config/devices/entry/vsys/entry/rulebase/nat/rules/entry[@name='" + fw_nat_rule_name1[0][0].text + "']")
                            fw_nat_rule_config1 = ET.fromstring('<root>' + xapi_fw.xml_result() + '</root>')
                            
                            for entry in fw_nat_rule_config1.iter('translated-address'): 
                                tr_addr=entry.tag
                                if (tr_addr == 'translated-address'):
                                    
                                    fw_nat_rule_tr_ad1 = fw_nat_rule_config1.find('entry/source-translation/dynamic-ip-and-port/translated-address/member').text
                                    try:
                                        translated_address_is_object=False
                                        ipaddress.ip_interface(fw_nat_rule_tr_ad1)
                                    except Exception as exception:
                                        translated_address_is_object=True
                                    if (translated_address_is_object):
                                        print("/config/devices/entry/vsys/entry/address/entry[@name='" + fw_nat_rule_tr_ad1 + "']")
                                        xapi_fw.show(xpath="/config/devices/entry/vsys/entry/address/entry[@name='" + fw_nat_rule_tr_ad1 + "']")
                                        fw_ip_obj_name1 = ET.fromstring('<root>' + xapi_fw.xml_result() + '</root>')
                                        output[fw_hostname]["nat_rule_1"]+=[{"name" : str(fw_nat_rule_name1[0][0].text), "public_ip_address" : str(fw_ip_obj_name1[0][0].text)}] 
                                    else:
                                        output[fw_hostname]["nat_rule_1"]+=[{"name" : str(fw_nat_rule_name1[0][0].text), "public_ip_address" : str(fw_nat_rule_tr_ad1)}]
                            for entry in fw_nat_rule_config1.iter('interface-address'): 
                                int_addr=entry.tag
                                if (int_addr == 'interface-address'):
                                    fw_nat_rule_tr_ad1 = fw_nat_rule_config1.find('entry/source-translation/dynamic-ip-and-port/interface-address/ip').text
                                    output[fw_hostname]["public_ip_address"] = fw_nat_rule_tr_ad1


                        if not no_nat_rule2:
                            
                            xapi_fw.show(xpath="/config/devices/entry/vsys/entry/rulebase/nat/rules/entry[@name='" + fw_nat_rule_name2[0][0].text + "']")
                            fw_nat_rule_config2 = ET.fromstring('<root>' + xapi_fw.xml_result() + '</root>')
                            
                            for entry in fw_nat_rule_config2.iter('translated-address'):
                                tr_addr=entry.tag
                                if (tr_addr == 'translated-address'):

                                    fw_nat_rule_tr_ad2 = fw_nat_rule_config2.find('entry/source-translation/dynamic-ip-and-port/translated-address/member').text
                                    try:
                                        translated_address_is_object=False
                                        ipaddress.ip_interface(fw_nat_rule_tr_ad2)
                                    except Exception as exception:
                                        translated_address_is_object=True
                                    if (translated_address_is_object):
                                        xapi_fw.show(xpath="/config/devices/entry/vsys/entry/address/entry[@name='" + fw_nat_rule_tr_ad2 + "']")
                                        fw_ip_obj_name2 = ET.fromstring('<root>' + xapi_fw.xml_result() + '</root>')
                                        output[fw_hostname]["nat_rule_2"]+=[{"name" : str(fw_nat_rule_name2[0][0].text), "public_ip_address" : str(fw_ip_obj_name2[0][0].text)}]
                                    else:
                                        output[fw_hostname]["nat_rule_2"]+=[{"name" : str(fw_nat_rule_name2[0][0].text), "public_ip_address" : str(fw_nat_rule_tr_ad2)}]
                            for entry in fw_nat_rule_config2.iter('interface-address'):
                                int_addr=entry.tag
                                if (int_addr == 'interface-address'):
                                    fw_nat_rule_tr_ad2 = fw_nat_rule_config2.find('entry/source-translation/dynamic-ip-and-port/interface-address/ip').text
                                    output[fw_hostname]["nat_rule_2"]+=[{"public_ip_address" : fw_nat_rule_tr_ad2 }]


#print ("\nDone")

#pprint.pprint(output)

def findkeys(node, kv):
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
               yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x

aligniplist=list(findkeys(output,'public_ip_address'))

f=open("/var/nginx/html/iprange/align_ips_list.txt", "w")
f.write("\n".join(list(set(aligniplist))))

f.close()
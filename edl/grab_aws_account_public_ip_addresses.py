# Grab AWS Public IPs (EC2) from owned AWS accounts, all regions, convert into PAN EDL format

import boto3, sys
from boto3 import ec2

# Provide Keys, as list of lists, as follow:

account_credentials = [['ACC_NAME1', 'ID 'KEY'],['ACC_NAME2', 'ID 'KEY']]      

aws_regions = ['us-east-1', 'us-west-1', 'us-west-2', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',
               'ap-northeast-1', 'eu-central-1', 'eu-west-1', 'sa-east-1']

list_of_ips = []
list_of_ips_from_instance = []

for account in account_credentials:
    for region in aws_regions:
        ec2 = boto3.client('ec2', region_name=region, aws_access_key_id=account[1],aws_secret_access_key=account[2])

        all_addresses = ec2.describe_addresses()
        for eip_dict in all_addresses['Addresses']:
            list_of_ips.append(eip_dict['PublicIp']+ "/32")

        all_instances = ec2.describe_instances()
        for reservation in all_instances['Reservations']:
            for instance in reservation['Instances']:
                if instance.get('PublicIpAddress') != None:
                    list_of_ips.append(instance['PublicIpAddress']+ "/32")

final_list_of_ips = []

for l in list_of_ips:
    if l not in final_list_of_ips:
        final_list_of_ips.append(l)

f = open('/usr/scripts/list_of_ips.txt','w')
for a3 in final_list_of_ips: f.write(a3+'\n')

f.close()

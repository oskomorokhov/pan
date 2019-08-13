#!/bin/bash
#parse AWS public IP ranges JSON and convert into PAN EDL format, bash

now=$(date)
yes | cp /var/nginx/html/iprange/aws_ips.txt /var/nginx/html/iprange/aws_ips.txt.tmp

string='<a href="https://host.domain.com/iprange/aws_ips.txt">"Click"</a><br>'
string2='<a href="https://host.domain.com/iprange/diff.log">"Click"</a><br>'
echo "Text format of the file is located here: $string" > /var/nginx/html/iprange/index.html
echo "History of IP addresses change is here: $string2" >> /var/nginx/html/iprange/index.html

curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | jq .prefixes | jq .[] | jq .ip_prefix | cut -d '"' -f 2 >> /var/nginx/html/iprange/index.html
sed -i 's/$/<br>/' /var/nginx/html/iprange/index.html

curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | jq .prefixes | jq .[] | jq .ip_prefix | cut -d '"' -f 2 > /var/nginx/html/iprange/aws_ips.txt

echo "$now :" >> /var/nginx/html/iprange/diff.log
comm -2 -3 --nocheck-order /var/nginx/html/iprange/aws_ips.txt /var/nginx/html/iprange/aws_ips.txt.tmp >> /var/nginx/html/iprange/diff.log

rm -f /var/nginx/html/iprange/aws_ips.txt.tmp

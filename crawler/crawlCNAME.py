import os
import sys
import dns
import time
import json
import requests
from ipwhois import IPWhois
from urllib.parse import urlparse



# total = int(sys.argv[1])
# nc = int(sys.argv[2])
# num = int(os.getenv("SLURM_ARRAY_TASK_ID"))

total = 3
nc = 1
num = 0

start = int(total/nc)*num
end = int(total/nc)*(num+1)

cache = {}


def getHostingCompany(ip):
    hostingCompanyLookupResult = IPWhois(ip).lookup_rdap(bootstrap=True, inc_nir=False)

    possibleNames = []

    try:
        possibleNames.append(hostingCompanyLookupResult['network']['name'])
    except:
        pass

    if 'objects' in hostingCompanyLookupResult:
        for i in hostingCompanyLookupResult['objects']:
            possibleNames.append(i)
            try:
                possibleNames.append(hostingCompanyLookupResult['objects'][i]['contact']['name'])
            except:
                pass
            try:
                for j in hostingCompanyLookupResult['objects'][i]['remarks']:
                    possibleNames.append(j['description'])
            except:
                pass
    

    return possibleNames

def cachedGetHostingCompany(ip):
    if ip not in cache:
        cache[ip] = getHostingCompany(ip)
        time.sleep(1)
    return cache[ip]

urls = []
with open("data/top-1m.csv", "r") as fin:
    for i, line in enumerate(fin):
        if i < start:
            continue
        if i >= end or i >= total:
            break
        urls.append(line.strip())

urls = ['api3.fox.com']

fout = open("results/cname/cname%d.txt" % num, "w")
for i, url in enumerate(urls):
    url = url.split(',')[1]
    print(i, url, file=sys.stderr)

    try:
        answers = dns.resolver.query(url, 'CNAME')
    except:
        answers = []

    data = {"url": url, "names": []}

    for cname in answers:
        dnsInfo = dns.resolver.query(cname, 'A').rrset
        ip = dnsInfo[0].to_text()

        for k in range(0, 3):
            try:
                data["names"] += cachedGetHostingCompany(ip)
                break
            except Exception as e:
                print(e, file=sys.stderr)
                time.sleep(1)

    fout.write(json.dumps(data)+"\n")
fout.close()

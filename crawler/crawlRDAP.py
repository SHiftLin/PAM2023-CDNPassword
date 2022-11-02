import os
import sys
import time
import json
import requests
from ipwhois import IPWhois


total = int(sys.argv[1])
nc = int(sys.argv[2])
num = int(os.getenv("SLURM_ARRAY_TASK_ID"))

start = int(total/nc)*num
end = int(total/nc)*(num+1)


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


ips = []
with open("data/IPs_rdap.txt", "r") as fin:
    for i, line in enumerate(fin):
        if i < start:
            continue
        if i >= end or i >= total:
            break
        ips.append(line.strip())


fout = open("results/rdap/rdap%d.txt" % num, "w")
for i, ip in enumerate(ips):
    print(i, ip, file=sys.stderr)

    data = {"ip": ip, "names": None}
    for k in range(0, 3):
        try:
            data["names"] = getHostingCompany(ip)
            time.sleep(1)
            break
        except Exception as e:
            print(e, file=sys.stderr)
            time.sleep(1)

    fout.write(json.dumps(data)+"\n")
fout.close()

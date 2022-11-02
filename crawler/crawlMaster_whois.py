import sys
import json
import time
import requests
import argparse
import whois
import random
import tldextract
from ipwhois import IPWhois


def getHostingCompany(ip):
    hostingCompanyLookupResult = IPWhois(ip).lookup_rdap(bootstrap=True, inc_nir=False)
    time.sleep(1)

    possibleNames = []

    possibleNames.append(hostingCompanyLookupResult['network']['name'])
    if hostingCompanyLookupResult['objects']:
        for i in hostingCompanyLookupResult['objects']:
            possibleNames.append(i)
            if hostingCompanyLookupResult['objects'][i]['contact']:
                possibleNames.append(hostingCompanyLookupResult['objects'][i]['contact']['name'])
            if hostingCompanyLookupResult['objects'][i]['remarks']:
                for j in hostingCompanyLookupResult['objects'][i]['remarks']:
                    possibleNames.append(j['description'])

    return possibleNames


def getWhoisOrg(domain):
    res = whois.whois(domain)
    org = None
    if "org" in res:
        org = res["org"]
    elif "admin_organization" in res:
        org = res["admin_organization"]
    else:
        print(res)
    time.sleep(1)
    return org


def processIPs(domain, ips, domains):
    results = {"ips": {}, "domains": {}}
    # for d in domains:
    #     ans = None
    #     for i in range(0, 3):
    #         try:
    #             ans = getWhoisOrg(d)
    #             break
    #         except Exception as e:
    #             print(e, file=sys.stderr)
    #             time.sleep(3)
    #     results["domains"][d] = ans

    for ip in ips:
        ans = None
        for i in range(0, 3):
            try:
                ans = getHostingCompany(ip)
                break
            except Exception as e:
                print(e, file=sys.stderr)
                time.sleep(3)
        results["ips"][ip] = ans

    return json.dumps(results)


def worker(urlServerAddress):
    postData = {}
    while True:
        response = requests.post(urlServerAddress, data=postData).json()
        if response == -1:
            return
        else:
            domain, ips, domains = response
            postData['resultData'] = processIPs(domain, ips, domains)
            postData['domain'] = domain


def startCrawling():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, help='port of the server', default=5001)
    parser.add_argument('-i', type=str, help='ip of the server', default="localhost")
    args = parser.parse_args()
    port = args.p
    ip = args.i

    worker("http://%s:%d" % (ip, port))


if __name__ == '__main__':
    # todo: allows debug while not ruining one site's experience: possibly just
    # detect if there's command line input
    time.sleep(random.randint(0,30))
    startCrawling()
    # print(processUrl("casemine.com"))
    # processUrl('apple.com')

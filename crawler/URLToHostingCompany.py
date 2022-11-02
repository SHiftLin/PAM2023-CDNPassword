from ipwhois import IPWhois
import tldextract
import dns.resolver
import whois
import time
from urllib.parse import urlparse

import json

def getDomain(url):
    return tldextract.extract(url).domain

def getWhois(url):
    return whois.whois(url)

# for amazon cloudfront, they label their server as AMAZO-CF whereas others are listed as EC2, or nothing at all
def getHostingCompany(url):
    # ext = tldextract.extract(url)
    # hostAddress = '.'.join(part for part in ext if part)
    hostAddress = urlparse(url).netloc

    dnsInfo = dns.resolver.query(hostAddress, 'A').rrset

    # # Maybe we can do something with it???
    # resolvedDomainName = tldextract.extract(dnsInfo.to_text()).domain

    hostingCompanyLookupResult = IPWhois(dnsInfo[0].to_text()).lookup_rdap(bootstrap=True, inc_nir=False)

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
# with open('cachedHoster.txt', encoding='utf-8') as f:
#     lookedUp = json.load(f)

lookedUp = {}

def getCountryCode(url):
    for _ in range(3):
        try:
            country = getWhois(url)['country']
            if country:
                return country
        except:
            pass
        time.sleep(5)

def lookup(url, lookedUp=lookedUp):
    domain = urlparse(url).netloc
    if not domain:
        raise 'Domain is empty'
    if domain in lookedUp:
        return lookedUp[domain]
    else: 
        ans = [False]
        for _ in range(3):
            try:
                ans = getHostingCompany(url)
                break
            except: 
                time.sleep(5)
        lookedUp[domain] = ans
        return ans

if __name__ == '__main__':
    # lookup('https://github.com')
    # lookup('https://idmsa.apple.com/appleauth/auth/signin?isRememberMeEnabled=true')
    getHostingCompany('https://idmsa.apple.com/appleauth/auth/signin?isRememberMeEnabled=true')
    getHostingCompany('https://dauth.user.ameba.jp')
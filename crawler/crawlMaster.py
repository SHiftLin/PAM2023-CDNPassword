import json
import time
import threading
import requests
import argparse

import tldextract

from browserController import crawlSingle, ErrorCodes
# from URLToHostingCompany import lookup, getCountryCode


CRAWL_RETRY_TIMES = 3


def processUrl(url):
    """handles a single url. Separated from worker for better testing experience

    Args:
        url (str): url to crawl

    Returns:
        str: result
    """
    processStartTime = time.time()

    # I should change the structure of result to have three indices
    result = ['', [], []]
    # ["github.com", [["password email ", "https://github.com/session", []]],
    # [1, 1, 2, 0, false, true, 1, ["buttonHTML"]]]]

    # if getCountryCode(url) == 'US':
    for i in range(CRAWL_RETRY_TIMES):
        # try adding www. at the last retry
        if i == CRAWL_RETRY_TIMES - 1 and result[1] == ErrorCodes.FAILED_TO_LOAD:
            url = 'www.' + url

        result = crawlSingle(url)
        if not isinstance(result[1], int):
            break
    crawlFinishTime = time.time()

    # if isinstance(result[1][0], list):
    #     # prevent memory from building up (actually it won't matter I think as
    #     # they are just text)
    #     lookedUp = {}
    #     for entry in result[1][0]:
    #         hostingProvider = lookup(entry[1], lookedUp)
    #         for i in hostingProvider:
    #             entry[2].append(i)
    # hostingProviderLookupFinishTime = time.time()

    # if not isinstance(result[1][0], int):
    #     result[1][1].append(getCountryCode(url))
    #     countryCodeLookupFinishTime = time.time()

    #     result[1][1].append(int(crawlFinishTime - processStartTime))
    #     result[1][1].append(int(hostingProviderLookupFinishTime - crawlFinishTime))
    #     result[1][1].append(int(countryCodeLookupFinishTime - hostingProviderLookupFinishTime))

    # else:
    #     result = [url, [ErrorCodes.OTHER, 'Skipped: not a US site']]
    result.append(int(crawlFinishTime - processStartTime))

    return json.dumps(result)


def worker(urlServerAddress):
    """the client that gets url from server and pass the url to processURL

    Args:
        urlServerAddress (str): ip or url for the url server
    """
    postData = {}
    while True:
        response = requests.post(urlServerAddress, data=postData).json()
        if response == -1:
            return
        else:
            idx, url = response
            postData['resultData'] = processUrl(url)
            postData['idx'] = idx


def startCrawling():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, help='port of the server', default=5000)
    parser.add_argument('-i', type=str, help='ip of the server', default="localhost")
    args = parser.parse_args()
    port = args.p
    ip = args.i

    worker("http://%s:%d" % (ip, port))


if __name__ == '__main__':
    # todo: allows debug while not ruining one site's experience: possibly just
    # detect if there's command line input
    startCrawling()
    # print(processUrl("casemine.com"))
    # processUrl('apple.com')

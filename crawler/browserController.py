import json
import random
import requests

import selenium
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import traceback
import time
import os
from urllib.parse import quote

from utils import *


with open("config.json") as f:
    config = json.load(f)

PATH_TO_DRIVER = config["chromeDriverPath"]

EMAIL = "awehof111@gmail.com"
# well, people usually say skeleton key, but this email is "skeleton" enough to me
SKELETONEMAIL = "testaccount@gmail.com"
PASSWORD = "8FQXeIIlTj"

DEBUG = False

STTIME = time.time()

webdriver.chrome.slientLogging = True


def log(msg):
    if DEBUG:
        print(
            "%s %s"
            % (time.strftime("%H:%M:%S", time.gmtime(time.time() - STTIME)), str(msg))
        )


recaptchaJS = loadJS("recaptcha.js")
evasionJS = loadJS("evasion.js")


def create_driver(proxy=False):

    proxies = [
        "128.173.237.66",
        "69.30.240.226:15002",
        "69.30.197.122:15002",
        "142.54.177.226:15002",
        "198.204.228.234:15002",
        "195.154.255.118:15002",
        "195.154.222.228:15002",
        "195.154.252.58:15002",
        "195.154.222.26:15002",
        "63.141.241.98:16001",
        "173.208.209.42:16001",
        "163.172.36.211:16001",
        "163.172.36.213:16001",
    ]

    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"performance": "ALL"}
    caps["loggingPrefs"] = {"performance": "ALL"}

    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation", "load-extension"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)

    chrome_options.add_experimental_option(
        "prefs", {"profile.default_content_setting_values.notifications": 2,}
    )

    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")

    # chrome_options.add_argument("--load-extension=" + os.path.abspath('RigRecaptcha/'))

    # chrome_options.add_argument('--disable-extensions')
    # chrome_options.add_argument("--disable-notifications")

    if not DEBUG:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument("--log-level=3")

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    )
    chrome_options.add_argument("window-size=1536,824")
    if proxy:
        chrome_options.add_argument(
            "--proxy-server={}".format(proxies[random.randint(0, 15)])
        )
    driver = None
    while driver == None:
        try:

            driver = webdriver.Chrome(
                executable_path=PATH_TO_DRIVER,
                options=chrome_options,
                desired_capabilities=caps,
            )
        except Exception as e:
            pass
    driver.set_page_load_timeout(30)

    # install different javascript
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "onbeforeunload = alert = prompt = confirm = function(){};"},
    )
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument", {"source": evasionJS}
    )
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument", {"source": recaptchaJS}
    )
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*://*/*recaptcha*"]})
    return driver


buttonDetectionScript = loadJS("detectButtons.js")


def detectButtons(driver):
    log("Detecting buttons...")

    buttons = driver.execute_script(buttonDetectionScript, DEBUG)

    removeItems = []

    # changed to :4 due to added user entry

    for key in ["email", "user", "password", "submit"]:
        i = buttons[key]
        for el in i[:]:
            if not userSeeable(el):
                i.remove(el)
                continue
            # change label to the element that it's point to
            if el.tag_name.lower().strip() == "label":
                removeItems.append(el)
                label = el
                try:
                    if el.get_attribute("for"):
                        el = driver.find_element_by_id(el.get_attribute("for"))
                    else:
                        el = el.find_element_by_css_selector(
                            'input, button, [role="button"]'
                        )
                except selenium.common.exceptions.NoSuchElementException:
                    pass
                # if it did not change at all
                if el == label or not userSeeable(el):
                    try:
                        # this has .click(), which might return an error
                        ActionChains(driver).move_to_element(label).click().perform()
                        el = driver.switch_to.active_element
                    except:
                        pass

                if not driver.execute_script(
                    "return arguments[0].matches('input:not([type]), input[type=text], input[type=email], input[type=password]')",
                    el,
                ):
                    # if el.tag_name.lower().strip() not in ['input', 'button']:
                    continue

                if el not in i:
                    i.append(el)

                # one more item for removal
                i.append(el)

                removeItems.append(el)

    for i in removeItems:
        for key in buttons:
            j = buttons[key]
            if i in j:
                j.remove(i)

    # merge email inputs and username inputs. not the best solution, but I think
    # it'll work for this proj
    for i in buttons["email"]:
        i.___wantsEmail = True
    for i in buttons["user"]:
        # since __eq__ is set for selenium elements, I can totally use "in"
        # keyword
        if i not in buttons["email"]:
            i.___wantsEmail = False
            buttons["email"].append(i)
    buttons["account"] = buttons["email"]
    del buttons["email"], buttons["user"]

    # post process login elements and sort it based on the score given by judge
    # (higher = better)
    currUrl = driver.current_url

    def judge(el):
        score = 0
        if isStale(el):
            return -999
            # score = -999
        if userSeeable(el):
            score += 8
        if el.tag_name.lower().strip() == "iframe":
            if score == 0:
                score = -999
            score += 4
        url = el.get_attribute("href") or el.get_attribute("src")
        if (
            url
            and not url.startswith("javascript:")
            and currUrl.split("#")[0] != url.split("#")[0]
        ):
            if isSameDomain(currUrl, url):
                score += 2
        elif not userChangeable(el):
            score = -999
        else:
            score += 2
        if DEBUG and score < 0:
            driver.execute_script('arguments[0].style.background = "gray";', el)
        return score

    # prevent from running forever but keep the most important stuff
    if len(buttons["login"]) > 40:
        buttons["login"] = buttons["login"][:20] + buttons["login"][-20:]

    for el in buttons["login"]:
        el.___score = judge(el)

    buttons["login"] = list(filter(lambda el: el.___score >= 0, buttons["login"]))

    buttons["login"].sort(key=lambda el: el.___score, reverse=True)

    if DEBUG:
        driver.execute_script(
            "debugButtons = arguments[0]; enableNextFunc(debugButtons);", buttons
        )

    return buttons


def toLoginPage(driver, btns, status):
    rtn = "samePage"
    currUrl = driver.current_url

    btnsHTML = driver.execute_script("return arguments[0].map(el=>el.outerHTML)", btns)
    btnsHTML.reverse()

    for i in btns:
        btnHTML = btnsHTML.pop()
        if isStale(i):
            continue
        url = i.get_attribute("href")
        elHash = "%d, %d, %d, %d" % (
            i.rect["x"],
            i.rect["y"],
            i.rect["width"],
            i.rect["height"],
        )
        if elHash in status["visitedEls"]:
            continue
        if (
            i.tag_name.lower().strip() == "a"
            and url
            and not url.startswith("javascript:")
            and currUrl.split("#")[0] != url.split("#")[0]
        ):
            try:
                i.click()
            except:
                driver.get(url)
        elif i.tag_name.lower().strip() == "iframe":
            try:
                switchToFrame(driver, i, status)
                # driver.switch_to.frame(i)
            except:
                continue
            log("iframe detected")
            rtn = "iframe"
        else:
            try:
                i.click()
            except:
                continue

        status["buttonClicked"].append(btnHTML)
        status["visitedEls"].append(elHash)
        time.sleep(1)
        if (
            len(driver.window_handles) > 1
            and driver.window_handles[len(driver.window_handles) - 1]
            != driver.current_window_handle
        ):
            driver.switch_to.window(
                driver.window_handles[len(driver.window_handles) - 1]
            )
            log("Another tab detected")
        if driver.current_url != currUrl and rtn == "samePage":
            # as we have entered a new page, current frame should get reset
            status["currentFrames"] = []
            rtn = "newPage"
        return rtn


# Example: https://sbu.ac.ir/
def checkHttpAuth(driver, status={}):
    log = driver.get_log("performance")
    for entry in log:
        message = json.loads(entry["message"])["message"]
        if (
            message["method"] == "Network.responseReceived"
            and message["params"]["response"]["status"] == 401
        ):
            url = message["params"]["response"]["url"]
            headers = message["params"]["response"]["headers"]
            auth = caseInsensitiveGet(headers, "WWW-Authenticate")
            if auth:
                status["httpAuth"] = auth
                for i in auth.split("\n"):
                    if i.split(" ")[0].lower() in [
                        "basic",
                        "digest",
                        "ntlm",
                        "negotiate",
                        "spdyproxy",
                        "mock",
                    ]:
                        viaArr = []
                        via = caseInsensitiveGet(headers, "via")
                        if via:
                            viaArr.append(via)
                        return [["password email ", url, viaArr]]


def getAccountServerURL(driver, skeletonEmailUsed=False):
    password = PASSWORD
    if skeletonEmailUsed:
        email = SKELETONEMAIL
    else:
        email = EMAIL.split("@")[0]

    passwords = [password, b64encode(password)]
    emails = [email, b64encode(email)]

    if skeletonEmailUsed:
        emails.append(quote(email, encoding="utf-8"))

    recaptchaCode = "hahahahahahahahahahahahhahahaaahahahaha"

    requestsOfInterest = {}
    requestsOfInterestIds = []

    log = driver.get_log("performance")
    for entry in log:
        message = json.loads(entry["message"])["message"]
        if message["method"] == "Network.requestWillBeSent":
            url = message["params"]["request"]["url"]

            if url.startswith("https://translate.googleapis.com"):
                continue

            if message["params"]["request"]["method"] == "POST":
                if "postData" in message["params"]["request"]:
                    stringOfInterest = message["params"]["request"]["postData"]
                else:
                    try:
                        stringOfInterest = driver.execute_cdp_cmd(
                            "Network.getRequestPostData",
                            {"requestId": message["params"]["requestId"]},
                        )["postData"]
                    except:
                        continue
                stringOfInterest += " " + url
            elif message["params"]["request"]["method"] == "GET":
                stringOfInterest = url
            else:
                # just for the sake of not forgetting anything
                stringOfInterest = url

            description = ""

            if strHasArrEl(stringOfInterest, passwords):
                description += "password "
            if strHasArrEl(stringOfInterest, emails):
                description += "email "
            if recaptchaCode in stringOfInterest:
                description += "recaptcha "

            if description:
                requestId = message["params"]["requestId"]
                if requestId in requestsOfInterest:
                    requestsOfInterest[requestId]["url"].append(url)
                    requestsOfInterest[requestId]["description"].append(description)
                else:
                    requestsOfInterestIds.append(requestId)
                    requestsOfInterest[requestId] = {
                        "description": [description],
                        "url": [url],
                        "via": [],
                    }

        elif message["method"] == "Network.responseReceived":
            requestId = message["params"]["requestId"]
            if strHasArrEl(requestId, requestsOfInterestIds):
                headers = message["params"]["response"]["headers"]
                via = caseInsensitiveGet(headers, "via")
                if via:
                    requestsOfInterest[requestId]["via"].append(via)

    requestUrls = []

    for i in requestsOfInterest:
        request = requestsOfInterest[i]
        for idx, val in enumerate(request["description"]):
            requestUrls.append(
                [request["description"][idx], request["url"][idx], request["via"]]
            )

    return requestUrls


def processFrame(driver, status, wait=True):
    log("Processing frame, current depth = %d" % status["depth"])

    httpAuth = checkHttpAuth(driver, status)
    if httpAuth:
        return httpAuth

    translatePage(driver)

    if wait:
        # the page has changed. wait for more time
        if waitUntilSelection(driver, "form", 10):
            time.sleep(5)
    else:
        # for waiting the page to translate
        time.sleep(1)

    switchToAutoFocusedInputElementFrame(driver, status)

    buttons = detectButtons(driver)

    status["recaptchaCount"] += len(buttons["recaptcha"])
    status["loginCount"] += len(buttons["login"])
    status["oauthCount"] += len(buttons["oauth"])

    # let's only continue if there's an email input
    if buttons["account"]:
        status["accountCount"] = len(buttons["account"])
        log("Account input detected. Sending fake accounts")

        urls = []

        skeletonEmailUsed = False

        # clear distracting loggingPrefs
        driver.get_log("performance")

        if not buttons["password"]:
            skeletonEmailUsed = True
            status["twoStepLogin"] = True

            accountInput = buttons["account"][0]

            account = SKELETONEMAIL
            if not accountInput.___wantsEmail:
                account = account.split("@")[0]
            try:
                accountInput.click()
                time.sleep(0.3)
            except:
                pass
            accountInput.send_keys(account)
            time.sleep(0.2)
            accountInput.send_keys(webdriver.common.keys.Keys.ENTER)

            time.sleep(5)
            buttons = detectButtons(driver)
            buttons["account"] = []

        status["passwordCount"] = len(buttons["password"])

        for i in buttons["account"]:
            if userChangeable(i):
                account = EMAIL
                if not i.___wantsEmail:
                    account = account.split("@")[0]
                try:
                    i.click()
                    time.sleep(0.3)
                except:
                    pass
                i.send_keys(account)
                i.send_keys(webdriver.common.keys.Keys.TAB)

        for i in buttons["password"]:
            if userChangeable(i):
                try:
                    i.click()
                    time.sleep(0.3)
                except:
                    pass
                i.send_keys(PASSWORD)
                # i.send_keys(webdriver.common.keys.Keys.TAB)
                status["passwordEntered"] = True

        if buttons["password"]:
            sendEnterKeyList = buttons["password"]
        else:
            sendEnterKeyList = buttons["account"]

        for i in buttons["recaptcha"]:
            driver.execute_script("arguments[0].click();", i)

        time.sleep(0.2)

        for i in sendEnterKeyList:
            if userChangeable(i):
                i.send_keys(webdriver.common.keys.Keys.ENTER)
                time.sleep(3)
                urls = getAccountServerURL(driver, skeletonEmailUsed)
                if urls:
                    return urls

        for i in buttons["submit"]:
            if userChangeable(i):
                try:
                    i.click()
                except selenium.common.exceptions.ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", i)
                time.sleep(3)
                urls = getAccountServerURL(driver, skeletonEmailUsed)
                if urls:
                    return urls

        # for sites that don't have anything after entering email address (e.g. google)
        urls = getAccountServerURL(driver, skeletonEmailUsed)
        if urls:
            return urls

        log("No request with email or password captured")
        return urls

    elif buttons["recaptcha"]:
        driver.execute_script("grecaptcha.___handleAll();")
        time.sleep(1)
        urls = getAccountServerURL(driver)
        if urls:
            return urls

    nextPageType = toLoginPage(driver, buttons["login"], status)

    # nothing found. Let's continue
    # iframe switch should not consume depth
    if nextPageType == "iframe" or nextPageType == "newTab":
        status["depth"] += 1
    if status["depth"] > 0:
        if isinstance(nextPageType, str) and nextPageType != "iframe":
            pass
            # translatePage(driver)

        # if we are switching to an iframe, we don't have to wait at all
        waitNeeded = nextPageType != "iframe"

        if nextPageType:
            log("Going to a login page")
            status["depth"] -= 1
            return processFrame(driver, status, waitNeeded)


def processPage(driver, url):

    log("Start processing %s" % url)

    url = normalizeURL(url)

    driver.get(url)

    urls = []

    initialDepth = 2

    status = {
        "accountCount": 0,
        "passwordCount": 0,
        "loginCount": 0,
        "recaptchaCount": 0,
        "oauthCount": 0,
        "twoStepLogin": False,
        "passwordEntered": False,
        "depth": initialDepth,
        "httpAuth": "",
        "buttonClicked": [],
        # entries below this will not go to the output status
        "currentFrames": [],
        "visitedEls": [],
    }

    urls = processFrame(driver, status)

    statusArr = [
        status["accountCount"],
        status["passwordCount"],
        status["loginCount"],
        status["recaptchaCount"],
        status["oauthCount"],
        status["twoStepLogin"],
        status["passwordEntered"],
        status["depth"],
        status["httpAuth"],
        status["buttonClicked"],
    ]

    if urls:
        log("Success")
        log(urls)
    else:
        log("Failed to detect login link. Exiting...")

    return (urls, statusArr)


def crawlSingle(url):
    driver = create_driver()
    try:
        result = processPage(driver, url)
    except selenium.common.exceptions.TimeoutException:
        result = (
            ErrorCodes.FAILED_TO_LOAD,
            "Error: page failed to load: %s" % traceback.format_exc(5),
        )
    except Exception as e:
        result = (ErrorCodes.CRASHED, "Error: program crashed: %s" % e)
    driver.quit()

    return (url, result)


if __name__ == "__main__":
    DEBUG = True
    driver = create_driver()
    url = "github.com"
    # driver.get('http://github.com')
    # rtn = getSelectedElement(driver)
    while True:
        result = processPage(driver, url)

# log = list(filter(lambda x: x['method'] == 'Network.requestWillBeSent', map(lambda x: json.loads(x['message'])['message'], driver.get_log('performance'))))
# log = list(map(lambda x: json.loads(x['message'])['message'], driver.get_log('performance')))


# TODO

# do some random mouse movement for 1 second

# [x] filter out ones that exist neither at the top nor at the bottom of the page

# [x] put judge function in js as i've now written isAtFront

# sogo: does not support phone login

# csdn: things are not working out after translation. the slash is gone, but
# signup has caps

# www.trustpilot.com facebook is a iframe button

# onlick especially ga push should be an indicator??

# job assigner -- log exiting job status

# fandom.com: rigrecaptcha not working

# okta.com not working: don't know your company url? should be signup

# [x] imgur search bar contains @user fixed: trash offset is now the same as
# visiable text offset (-99 vs 99) so it's now trash

# [x] apple.com pressing enter too fast will lead to failure in loading

# [x] khanacademy not working: login-signup-root is not picked up by the current "/"
# "or" rule (actually, it's caused by signup form detection scheme) potential
# fix: ensure that the form must contain its inputs?

# improve current signup detection: currently the multiplier is -99 and it is
# only designed to detect natural language instead of programming text. Should I
# change it to .99 if the category belongs to non spoken word? Also, the rule
# itself is greatly diverged from the original design, so further moniter is
# required

# [x] does switchToFrame work for nested frames?? fix: keep track of the frame
# sequence

# [x] **distinguish username from email** (chase.com, livejasmin.com, quizlet.com),
# email in cookie (actually not the cause), khanacademy not working (fixed)

# [x] headless mode cannot use extension, but the evasion script can handle v2
# invisiable, and v3 recaptcha maybe just use Fetch.enable instead? it should
# also work for content script as well

# [x] vimeo javascript issue caused by string.test. how to isolate the
# environment? (basically how to create an extension....)

# [x] washingtonpost.com sign in button contains in a sign up form

# [x] cnbc.com there's an iframe within an iframe with almost no hint of the
# signin at the iframe element. must use context instead -- fixed by identifying
# pre-focused element

# [x] https://www.cnet.com/ context required. the login button only shows "use
# email"

# [x] vimeo registeration forms contains login box

# [x] imdb create a new account has signin and signup keywords - fixed by
# changing signup to a trash keyword but ignoring "or" "/" keywords that might
# lead to two responses

# [x] ups.com cannot detect login button since it's inside a signup form. fix:
# separate login button detection from normal form detection

# currently evasion, recaptcha is not running on newly opened page as selenium
# cannot attach cdp event listener

# wontfix: washingtonpost.com does not have testaccount@something

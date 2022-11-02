import tldextract
import base64
import re
import time
import selenium

class ErrorCodes:
    FAILED_TO_LOAD = -1
    CRASHED = -2
    OTHER = -3


def caseInsensitiveGet(dic, key):
    key = key.lower()
    for i in dic:
        if i.lower() == key:
            return dic[i]


def loadJS(path, pathBase="src/crawler/js/"):
    """load javascript string from a file

    Args:
        path (str): the path to the javascript file
        pathBase (str): the base path

    Returns:
        str: the content of the js file with content wrapped in /*${}*/ revealed
    """
    with open(pathBase + path, encoding="utf-8") as f:
        return re.sub(r"/\*\$\{(.*?)\}\*/", r"\1", f.read())


def b64encode(s):
    return str(base64.b64encode(bytes(s, "utf-8")), "utf-8")


def strHasArrEl(s, arr):
    for i in arr:
        if i in s:
            return True


def isSameDomain(url1, url2):
    if url1 and url2:
        return (
            tldextract.extract(url1).domain.lower()
            == tldextract.extract(url2).domain.lower()
        )


def waitUntilSelection(driver, selector, waitTime):
    POOLTIME = 0.5
    waitInterval = int(waitTime / POOLTIME) - 1
    for i in range(waitInterval):
        time.sleep(POOLTIME)
        if driver.find_elements_by_css_selector(selector):
            return True


def normalizeURL(url):
    return "http://" + url.split("//")[-1]


def isStale(el):
    try:
        el.get_attribute("readonly")
    except selenium.common.exceptions.StaleElementReferenceException:
        return True


def userSeeable(el):
    if isStale(el):
        return False
    readOnly = el.get_attribute("readonly")
    return not readOnly and el.is_displayed()


def userChangeable(el):
    return userSeeable(el) and el.is_enabled()


def switchToFrame(driver, frames, status):
    # overloading this equation: frames can be both single element, or a list
    # recording how to get to this list
    if isinstance(frames, list):
        status["currentFrames"] = frames
        driver.switch_to.default_content()
    else:
        status["currentFrames"].append(frames)
        frames = [frames]
    for frame in frames:
        driver.switch_to.frame(frame)


def switchToAutoFocusedInputElementFrame(driver, status={"currentFrames": []}):
    currentFrames = status["currentFrames"]

    element = driver.switch_to.active_element
    while element.tag_name == "iframe":
        switchToFrame(driver, element, status)
        element = driver.switch_to.active_element

    if element.tag_name != "input":
        switchToFrame(driver, currentFrames, status)


def runScirptInIsolatedWorld(driver, script, worldName=""):
    # I had to use url to identify frame, which is absolutely a horribe design
    # of selenium
    url = driver.execute_script("return String(location).split('#')[0];")

    frameTree = driver.execute_cdp_cmd("Page.getFrameTree", {})["frameTree"]

    for i in [frameTree] + frameTree.get("childFrames", []):
        frame = i["frame"]
        if frame["url"] == url:
            currentFrameId = frame["id"]
            break

    isolatedWorldId = driver.execute_cdp_cmd(
        "Page.createIsolatedWorld",
        {
            "frameId": currentFrameId,
            # well, it seems like devtools protocol does not provide setting the
            # origin of the isolated world (unlike how they implement the
            # translation part), so some sites will that has CSP enabled will not
            # have translation
            # also, i still cannot figure out why grantUniveralAccess doesn't work
            "grantUniveralAccess": True,
            "worldName": worldName,
        },
    )["executionContextId"]

    driver.execute_cdp_cmd(
        "Runtime.evaluate",
        {
            "expression": "(function() {%s})();" % script,
            "contextId": isolatedWorldId,
            # 'awaitPromise': True,
            # 'preview': True
            # 'returnByValue': True
        },
    )


translateJS = loadJS("translate.js")


def translatePage(driver):
    runScirptInIsolatedWorld(driver, translateJS, "translate")

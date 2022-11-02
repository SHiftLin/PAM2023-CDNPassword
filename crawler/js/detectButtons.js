let DEBUG = true;

let LOG = true;

/*${DEBUG = arguments[0]}*/

/*${LOG = arguments[1]}*/

// all utilities are here. they should do exactly what their name implies

let commonRegex = {
    dashUnderscore: /[\-_]/gi,
    nonWordCharacters: /[^a-z0-9]+/gi,
};

function combineWords(arr1, arr2) {
    let out = [];
    arr1.forEach((word1) => {
        arr2.forEach((word2) => {
            out.push(`${word1}${word2}`);
            out.push(`${word1} ${word2}`);
        });
    });
    return out;
}

function containsAny(dict, words) {
    for (let i of words) {
        if (dict[i]) {
            return true;
        }
    }
    return false;
}

// there's a great chance that both url and class name are using camelCase, so
// let's break them
function handleURLProperty(prop) {
    return function handleURL(el) {
        if (!el[prop]) return;
        // search entry often contains lots of trash options, such as
        // "keepSignedIn=0" or something along that line, so it's crucial to
        // remove them
        let path = el[prop].split("?")[0].split("#")[0].replace(currURL, "");
        let search = el[prop].split("?")[1] || "";
        try {
            search = decodeURIComponent(search);
        } catch (e) {}
        search = search.replace(commonRegex.dashUnderscore, " ");
        if (search) {
            for (let i of trashKeyword) {
                search = search.replace(i, "");
            }
            for (let i of signUpKeyword) {
                search = search.replace(i, "");
            }
        }

        let url = path + " " + search;

        return url.replace(/([a-z0-9])([A-Z])/g, "$1 $2");

        // return el[prop] && el[prop].split('?')[0].split('#')[0].replace(currURL, '');
        // return el[prop] && decodeURIComponent(el[prop].replace(currURL, '')).replace(/([a-z0-9])([A-Z])/g, '$1 $2');
    };
}

function processClassName(el) {
    return (
        typeof el.className === "string" &&
        el.className.replace(" ", "|").replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    );
}

function processScriptingProperty(prop) {
    let fcn = function (el) {
        return (
            typeof el[prop] === "string" &&
            el[prop].replace(/([a-z0-9])([A-Z])/g, "$1 $2")
        );
    };
    if (DEBUG) {
        Object.defineProperty(fcn, "name", {
            value: "process" + prop.charAt(0).toUpperCase() + prop.slice(1),
        });
    }
    return fcn;
}

// restrict the maximum length of innertext: at most 5 words natural language so
// they usually won't have camelCase

// using nonwordcharacters because we would like to count / as a separator of
// word as well
function isInnerTextTooLong(el) {
    let text = el.innerText || "";
    return text.split(commonRegex.nonWordCharacters).length > 5;
}

function processTitle(el) {
    let text = el.title || "";
    if (text.split(commonRegex.nonWordCharacters).length > 5) text = "";
    return text;
}

function highLight(el, type) {
    const colors = {
        email: "red",
        user: "orange",
        password: "yellow",
        submit: "green",
        login: "blue",
        signup: "#rgba(228, 239, 30, 0.45)",
        null: "black",
        trash: "black",
    };
    el.style.background = colors[type] || "brown";
    el.style.boxShadow = "0 0 10px 5px black";
}

function isFunction(f) {
    return typeof f === "function";
}

// from jQuery (stolen from stackoverflow)
function isVisiable(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
}

// this one should not raise an error, as it's rect should always return DOMRect
// with valid number
function isAtFront(el) {
    const rect = el.getBoundingClientRect();
    const x = rect.x + rect.width / 2;
    const y = rect.y + rect.height / 2;
    const pointEl = document.elementFromPoint(x, y);
    return el.contains(pointEl);
}

function isInMiddleOfPage(el) {
    const rect = el.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const scrollTop = window.pageYOffset - document.documentElement.clientTop;
    return (
        rect.top + scrollTop > viewportHeight * 1.5 &&
        rect.bottom + scrollTop < document.body.scrollHeight - viewportHeight * 1.5
    );
}

/**
 * identify if a string contains any element inside of the array of string and
 * regular expression
 * @param {String} str the string to be tested
 * @param {(String|RegExp)[]} arr the array of valid string or regular
 * expression
 * @returns {Boolean}
 */
function stringHasArrEl(str, arr) {
    return arr.reduce((acc, cur) => {
        return (
            acc ||
            (typeof cur === "string"
                ? str.indexOf(cur) !== -1
                : cur.test && cur.test(str))
        );
    }, false);
}

// key words used to identify each element

// Each element: (type, [desiredValues], [undesiredValues], trashScoreModifier)
let signInCombination = combineWords(["sign", "log"], ["in", "on"]);

// prettier-ignore
let signupIdentifier = [
    ['signUp', ['signup', 'sign up', 'newsletter', 'register', 'registration', 'subscribe'], ['registered']],
    ['signIn', [...signInCombination, 'auth'], ['mobile']]
];

let oauthKeyword = [
    "with google",
    "with facebook",
    "with apple",
    "with amazon",
    "with twitter",
    "with twitch",
];

let signupAttributes = ["id", "className"];

// prettier-ignore
let trashKeyword = [
    // with some companies
    ...oauthKeyword,
    // legal stuff 
    'terms', 'agreement', 'policy', 'privacy',
    // forgot account
    'recover', 'lost', 'forget', 'forgot', 'remember', 'confirmation', 'don\'t know',
    // stay signed in
    'stay', 'keep', 'signed', 
    // paywall/subscription
    'subscribe', 'paywall', 'news', 'email form', 
    // misc
    'feedback', 'search', 'ads'
];

// prettier-ignore
let signUpKeyword = ['signup', 'sign up', 'register', 'registration', 'create', 'join', 'new'];

// the fourth item is used to compute if an element is trash or not signup is
// only -0.99 since some login buttons have "sign in or sign up", so that low
// penalty would allow those ones to pass the test

// Change: it turns that this will let cases like create an account
// prettier-ignore
let typeIdentifier = [
    ['trash', trashKeyword, [], -999],
    ['oauth', oauthKeyword, []],
    ['signUp', signUpKeyword, ['/', 'or'], -99],
    ['account', ['account', 'user', /\buid|uid\b/, 'online id'], ['fluid', 'reg', 'news', 'accountant', 'youtube.com/user', 'user guide']],
    ['email', ['mail'], ['mailto']],
    ['password', ['password'], ['passport', 'reg']],
    ['next', ['next', 'continue'], ['blog', 'keep', 'signed', 'with']],
    ['signIn', [...signInCombination, 'auth'], ['author', 'oauth']],
]

let visiableAttributes = ["placeholder", "value", "innerText"];

let valuableAttributes = [
    // natural language
    processTitle,
    "placeholder",
    "value",
    "innerText",

    // scripting language
    processScriptingProperty("id"),
    processScriptingProperty("onclick"),
    processClassName,
    handleURLProperty("href"),
    handleURLProperty("src"),

    // misc
    "type",
    "autocomplete",
    "name",
];

let currURL = location.href.split("?")[0].split("#")[0];

function determineType(el, identifier, attributes) {
    // well, i didn't intend to write such a messy code, but i have to make sure
    // that identifiers are going in the right order...

    let out = {};

    // initialize the number of occurences
    for (let i of identifier) {
        out[i[0]] = 0;
    }

    // fetch attribute only once so it is faster it was actually a great speed
    // boost when this first written in python but since it's now in javascript,
    // it's actually not that significant
    let attrs = attributes.map((e) => {
        let attr;
        if (isFunction(e)) {
            attr = e(el);
        } else {
            attr = el[e];
        }
        // why did i do this??? was it just for urls? NVM, they are for _-

        // replacing only dash and underscore because other characters would
        // mean a shift in meaning block

        // attr = attr && String(attr).replace(/[^a-z0-9\/]/ig, ' ');
        attr = attr && String(attr).replace(commonRegex.dashUnderscore, " ");
        return attr;
    });

    // initialize trash score
    let attrsScore = attributes.map((e) => 0);

    if (DEBUG) {
        el.dataset.CDNdebugger = "";
    }

    for (let j of identifier) {
        for (let i in attributes) {
            let prop = attrs[i];

            if (prop) {
                prop = String(prop).trim().toLowerCase();
                if (
                    !stringHasArrEl(prop, j[2]) &&
                    stringHasArrEl(prop, j[1]) &&
                    j[0]
                ) {
                    if (DEBUG) {
                        el.dataset.CDNdebugger += `${j[0]}, ${
                            attributes[i].name || attributes[i]
                        }; `;
                    }

                    // manually assigns a higher score for innerText, as that's
                    // what users see
                    let multiplier =
                        visiableAttributes.indexOf(attributes[i]) > -1 ? 99 : 1;

                    // for deciding whether it's trash
                    attrsScore[i] += (j[3] || 1) * multiplier;

                    // this score is only used for login buttons for ranking,
                    // and for other ones, it only informs if they exists or not
                    out[j[0]] += 1 * multiplier;
                }
            }
        }
    }
    // if the sum of trash score is below or equal to zero, then tag it as a
    // trash element by saying trash i only mean that it does not belong to our
    // needs
    out.isTrash =
        0 >=
        attrsScore.reduce((acc, cur) => {
            return acc + cur;
            // if (cur > 0) {
            //     return acc + 1;
            // } else {
            //     return acc + cur;
            // }
        });
    return out;
}

/**
 * get the visually largest text within an element (determined by css value
 * fontSize)
 * @param {HTMLElement} root the element that you want to find the visually
 * largest text within
 */
function getLargestText(root) {
    const containsWordRe = /\w/i;

    let treeWalker = document.createTreeWalker(
        root,
        NodeFilter.SHOW_ELEMENT + NodeFilter.SHOW_TEXT
    );
    let maxFontSize = -1;
    let outText = "";
    let el;
    while ((el = treeWalker.nextNode())) {
        let node, text;
        if (el.nodeType === Node.TEXT_NODE) {
            text = el.textContent;
            node = el.parentNode;
        } else if (el.matches("input[type=button], input[type=submit]")) {
            text = el.value;
            node = el;
        } else {
            continue;
        }
        let fontSize = parseFloat(getComputedStyle(node)["fontSize"]);
        if (
            isVisiable(node) &&
            fontSize >= maxFontSize &&
            containsWordRe.test(text)
        ) {
            if (fontSize > maxFontSize) {
                outText = "";
                maxFontSize = fontSize;
            }
            outText += " " + text;
        }
    }
    return outText;
}

/**
 * identify if an element is a login form by examining its largest visiable text
 * @param {HTMLElement} el the target element
 */
function isLoginByLargestText(el) {
    return stringHasArrEl(getLargestText(el).toLowerCase(), signInCombination);
}

function detectButtons() {
    let inputs = {
        email: [],
        user: [],
        password: [],
        submit: [],
        login: [],
        recaptcha: [],
        oauth: [],
    };

    const emailPasswordSelector =
        "input:not([type]), input[type=text], input[type=email], input[type=password], label";

    const loginSelector =
        'input[type="button"], input[type="submit"], a[href], button, iframe';

    // it walks the entire dom tree for us. it's a fast implementation (and the
    // one that won't go wrong)
    const treeWalker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_ELEMENT
    );

    let el;
    let processedParent;

    // if an element is a child of signup form, it still might contain login
    // link (e.g. ups.com). My solution below is quite ugly, and I cannot find a
    // better one
    let signUpFormParent;
    let hasLoginForm = false;

    while ((el = treeWalker.nextNode())) {
        // in chrome, $0 means the last selected element in the elements panel
        if (DEBUG && window.$0 && window.$0debug && el === $0) debugger;

        // if it has been decided that a parent won't have any child that's of
        // interest to us, then skip all its children
        if (processedParent && processedParent.contains(el)) continue;

        // I have not seen any website where they put login box in the middle of
        // page, and it should be useful in some news sites
        if (isVisiable(el) && isInMiddleOfPage(el)) {
            processedParent = el;
            continue;
        }

        if (el.matches(emailPasswordSelector)) {
            if (signUpFormParent && signUpFormParent.contains(el)) continue;

            // this is for labels
            if (isInnerTextTooLong(el)) continue;

            const elType = determineType(
                el,
                typeIdentifier,
                valuableAttributes
            );

            if (elType.isTrash) continue;

            if (containsAny(elType, ["password"])) {
                // if it has a hidden password field, then it basically means
                // that ther's a login form as password input is used almost
                // exclusively for this purpose
                hasLoginForm = true;

                // but we only take the visiable ones (the ones that users can
                // see) the second part is for wayfair.com
                if (
                    isVisiable(el) &&
                    (el.tagName.toLowerCase() !== "input" ||
                        el.offsetHeight >= 16)
                ) {
                    inputs.password.push(el);
                }
            } else if (
                isVisiable(el) &&
                containsAny(elType, ["account", "email", "signIn"])
            ) {
                if (containsAny(elType, ["account", "signIn"])) {
                    hasLoginForm = true;
                }
                if (containsAny(elType, ["email"])) {
                    inputs.email.push(el);
                } else {
                    inputs.user.push(el);
                }
            }

            // if a website would like user to click on something, it should
            // 1) be a button, or a hyperlink
            // 2) or be visiable to users and change cursor to pointer style when
            //    hovering
        } else if (
            (isVisiable(el) && getComputedStyle(el).cursor === "pointer") ||
            el.matches(loginSelector)
        ) {
            if (isInnerTextTooLong(el)) continue;

            const elType = determineType(
                el,
                typeIdentifier,
                valuableAttributes
            );

            // svg is breaking my code as everything related to it is
            // nonstandard (as it has its own namespace)
            if (el.tagName.toLowerCase() === "svg") {
                processedParent = el;
                continue;
            }

            if (elType.oauth) {
                inputs.oauth.push(el);
                continue;
            }

            if (elType.isTrash) continue;

            if (
                inputs.email.length &&
                containsAny(elType, [/*'account', */ "signIn", "next"])
            ) {
                processedParent = el;
                inputs.submit.push(el);
            }
            if (containsAny(elType, ["account", "signIn", "email"])) {
                processedParent = el;
                // sort login buttons based on how many features do they have
                // (one attribute = 1pt but innerText = 100pt)
                inputs.login.push([el, elType["account"] + elType["signIn"]]);
            }
        } else if (signUpFormParent && signUpFormParent.contains(el)) {
            continue;
            // for recaptcha buttons. info provided by rig recaptcha extension
        } else if (el.matches("[data-cdn-click-required]")) {
            inputs.recaptcha.push(el);
        } else {
            // for determining if a div is created for signing up. if it is,
            // then just ignore its children
            const elType = determineType(
                el,
                signupIdentifier,
                signupAttributes
            );
            if (!elType.signIn && elType.signUp && !isLoginByLargestText(el)) {
                // prune the search tree for login field
                signUpFormParent = el;
                if (DEBUG) {
                    el.style.background = "gray";
                }
            }
        }
    }

    // each one el[1] originally contians how many times the keyword has been
    // mentioned. Adding isAtFront(el[0]) * 2 means +2 mention when it's at the front
    inputs.login.forEach((el) => (el[1] += isAtFront(el[0]) * 2));

    inputs.login.sort((a, b) => b[1] - a[1]);

    inputs.login = inputs.login.map((el) => el[0]);

    if (inputs.email.length && !hasLoginForm) {
        if (DEBUG) {
            inputs.email.forEach((el) => (el.style.background = "gray"));
        }
        inputs.email = [];
        // inputs.login = inputs.login.concat(inputs.submit);
        // inputs.submit = [];
    }
    if (DEBUG) {
        for (let i in inputs) {
            inputs[i].forEach((el) => highLight(el, i));
        }
    }

    return inputs;
    // [inputs.email, inputs.user, inputs.password, inputs.submit, inputs.login, inputs.recaptcha];
}

if (DEBUG) {
    if (window.$0debug === undefined) {
        $0debug = false;
    }
    enableNextFunc = function (resultDict) {
        let idx;
        let loginArr = resultDict.login;
        nextLogin = function (i) {
            loginArr[idx] &&
                (loginArr[idx].style.boxShadow = "0 0 10px 5px black");
            if (i === undefined) {
                idx++;
            } else {
                idx = i;
            }
            if (idx >= loginArr.length) {
                idx = 0;
            }
            loginArr[idx] &&
                (loginArr[idx].style.boxShadow = "0 0 10px 5px aqua");
            console.log(idx);
            return loginArr[idx];
        };
        console.log(resultDict);
        console.log(nextLogin(0));
    };
}

let rtn = detectButtons();

if (LOG) {
    console.log(rtn);
}

/*${return rtn}*/

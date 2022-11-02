let DEBUG = true;

let LOG = true;

/*${DEBUG = arguments[0]}*/

/*${LOG = arguments[1]}*/

let commonRegex = {
    dashUnderscore: /[\-_]/gi,
    nonWordCharacters: /[^a-z0-9]+/gi,
    camel: /([a-z0-9])([A-Z])/g
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

let oauthKeyword = [
    "with google",
    "with facebook",
    "with apple",
    "with amazon",
    "with twitter",
    "with twitch",
];

let trashKeyword = [
    // with some companies
    // ...oauthKeyword,
    // legal stuff 
    'terms', 'agreement', 'policy', 'privacy',
    // forgot account
    'recover', 'lost', 'forget', 'forgot', 'remember', 'confirmation', 'don\'t know',
    // stay signed in
    'stay', 'keep', 'signed',
    // paywall/subscription
    'subscribe', 'paywall', 'news', 'email form',
    // misc
    'feedback', 'search', 'ads', 'mailto:'
];

let signupAttributes = ["id", "className", handleURLProperty('action')];

let signupIdentifier = [
    ['trash', trashKeyword, ['keeper']],
    ['signup', ['signup', 'sign up', 'newsletter', 'register', 'registration', 'subscribe', 'create', 'join', 'new '], ['/', /\bor\b/, 'registered']]
    // ['signIn', [...signInCombination, 'auth'], ['mobile']]
];

let signInCombination = combineWords(["sign", "log"], ["in", "on"]).concat(['to come in']);

let typeIdentifier = [
    ['trash', trashKeyword, ['keeper']],
    ['oauth', oauthKeyword, []],
    ['account', ['account', 'user', /\buid|uid\b/, 'online id', 'credential'],
        ['fluid', 'reg', 'news', 'accountant', 'youtube.com  user', 'user guide', 'accountable', 'user content']
    ],
    ['email', ['mail'],
        ['mailto']
    ],
    ['password', ['pass'],
        ['passport', 'reg']
    ],
    ['next', ['next', 'continue'],
        ['blog', 'keep', 'signed', 'with']
    ],
    ['login', [...signInCombination, 'auth'],
        ['author', 'oauth']
    ],
]

function stringHasArrEl(str, arr) {
    return arr.reduce((acc, cur) => {
        return (
            acc || ((typeof cur === "string" ? str.indexOf(cur) !== -1 : cur.test && cur.test(str)))
        );
    }, false);
}

function processClassName(el) {
    return (
        typeof el.className === "string" &&
        el.className.replace(" ", "|").replace(commonRegex.camel, "$1 $2")
    );
}

function processScriptingProperty(prop) {
    let fcn = function (el) {
        return (
            typeof el[prop] === "string" && el[prop].replace(commonRegex.camel, "$1 $2")
        );
    };
    return fcn;
}

function processTitle(el) {
    let text = el.title || "";
    if (text.split(commonRegex.nonWordCharacters).length > 5) text = "";
    return text;
}

function handleURLProperty(prop) {
    let currURL = location.href.split("?")[0].split("#")[0];
    return function handleURL(el) {
        if (typeof (el[prop]) != "string") return;
        // search entry often contains lots of trash options, such as
        // "keepSignedIn=0" or something along that line, so it's crucial to
        // remove them
        let path = el[prop].split("?")[0].split("#")[0].replace(currURL, "");
        let search = el[prop].split("?")[1] || "";
        try {
            search = decodeURIComponent(search);
        } catch (e) { }
        search = search.replace(commonRegex.dashUnderscore, " ");
        let url = path + " " + search;
        url = url.replaceAll("/", "  ");

        return url.replace(commonRegex.camel, "$1 $2");
    };
}


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

function isVisible(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
}

function isSigninBySubmit(el) {
    let out = false;
    el.querySelectorAll('[type=submit]').forEach((el) => {
        let txt = String(el.value || el.innerText).toLowerCase();
        out |= isVisible(el) && stringHasArrEl(txt, signInCombination);
    });
    return out;
}

function isSigninByLargestButton(el) {
    let largestEl = null;
    let largestArea = 0;
    el.querySelectorAll('[role=button], button, input[type=button]').forEach((el) => {
        if (isVisible(el) && (el.offsetHeight * el.offsetWidth >= largestArea)) {
            largestArea = el.offsetHeight * el.offsetWidth;
            largestEl = el;
        }
    });
    return largestEl && stringHasArrEl(String(largestEl.value || largestEl.innerText).toLowerCase(), signInCombination);
}

function getRelativeLocation(el) {
    const rect = el.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;
    return [
        rect.left / viewportWidth, rect.top / viewportHeight,
        rect.right / viewportWidth, rect.bottom / viewportHeight
    ]
}

function determineType(el, identifier, attributes) {
    let out = {};
    for (let i of identifier)
        out[i[0]] = 0;

    let debugText = "";

    let attrs = attributes.map((f) => {
        let attr = (typeof f === "function") ? f(el) : el[f];
        attr = attr && String(attr).replace(commonRegex.dashUnderscore, " ").toLowerCase();
        return attr;
    });

    let flag = false;
    for (let i of identifier)
        for (let j = attrs.length - 1; j >= 0 ; j--) {
            let attr = attrs[j];
            if (attr && !stringHasArrEl(attr, i[2]) && stringHasArrEl(attr, i[1])) {
                if (DEBUG) debugText += `${i[0]}, ${attributes[j].name || attributes[j]}; `;
                out[i[0]] += 1, flag = true;
            }
        }

    if (DEBUG && flag) el.dataset.CDNdebugger = debugText;

    return [out, flag];
}

function inSignUp(signups, el) {
    while (signups.length > 0 && !signups[signups.length - 1].contains(el))
        signups.pop();
    return signups.length
}

function prelimFilter() {
    const treeWalker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_ELEMENT
    );

    const emailPasswordSelector =
        // "input:not([type]), input[type=text], input[type=email], input[type=password], label";
        "input:not([type=button]):not([type=checkbox]):not([type=color]):not([type=date]):not([type=datetime-local]):not([type=file]):not([type=hidden]):not([type=image]):not([type=month]):not([type=number]):not([type=radio]):not([type=range]):not([type=reset]):not([type=search]):not([type=submit]):not([type=tel]):not([type=time]):not([type=url]):not([type=week])";
    const loginSelector =
        'input[type="button"], input[type="submit"], a[href], button, iframe';
    const labelSelector = "label";

    let signups = []
    let inputs = []
    let stacks = []
    let dfsSeq = {}
    let seqL = 0;
    let uid = 0;
    let el;
    let labelFeature = {}

    while ((el = treeWalker.nextNode())) {
        if (DEBUG && window.$0 && window.$0debug && el === $0) debugger;
        if (el.tagName.toLowerCase() === "svg")
            continue

        let [elType, flag] = determineType(el, signupIdentifier, signupAttributes);
        if (elType["trash"] > 0) continue;
        if (elType["signup"] > 0 && !isSigninBySubmit(el) && !isSigninByLargestButton(el)) {
            inSignUp(signups, el);
            signups.push(el)
        }

        if (el.matches(emailPasswordSelector) || el.matches(loginSelector) || el.matches(labelSelector) || 
            getComputedStyle(el).cursor === "pointer") {
            let [features, flag] = determineType(el, typeIdentifier, valuableAttributes); //keyword matching
            if (features["trash"] > 0) continue;
            if (!flag) continue;

            if (el.tagName.trim().toLowerCase() == "label" && el.getAttribute("for") != null) { //label to input
                labelFeature[el.getAttribute("for")] = features;
                continue;
            }

            [features["loc_left"], features["loc_top"], features["loc_right"], features["loc_bottom"]] = getRelativeLocation(el);
            if (features["loc_top"] > 1.5) continue;
            // if (features["loc_bottom"] < 0 || features["loc_right"] < 0) continue;
            // if (features["loc_bottom"] - features["loc_top"] == 0 || features["loc_right"] - features["loc_left"] == 0) continue;

            let id = el.getAttribute("id")
            if (id != null && id in labelFeature)
                for (let key in labelFeature[id])
                    features[key] += labelFeature[id][key]

            features["tag"] = el.tagName.trim().toLowerCase();
            features["signup"] = inSignUp(signups, el)
            let text = el.innerText || "";
            features["innertextLength"] = text.split(commonRegex.nonWordCharacters).length;
            features['emailPasswordSelected'] = el.matches(emailPasswordSelector);
            features['className'] = String(el.className);
            features['type'] = String(el.type);

            // delete features["trash"]
            uid += 1;
            inputs.push([el, features, '', el.outerHTML, uid]) //label as '' initially

            while (stacks.length > 0 && !stacks[stacks.length - 1][0].contains(el)) {
                dfsSeq[stacks[stacks.length - 1][1]][1] = seqL;
                seqL += 1;
                stacks.pop();
            }
            dfsSeq[uid] = [seqL, -1];
            seqL += 1;
            stacks.push([el, uid]);
        }
    }
    while (stacks.length > 0) {
        dfsSeq[stacks[stacks.length - 1][1]][1] = seqL;
        seqL += 1
        stacks.pop();
    }
    return [inputs, dfsSeq]
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


let rtn = prelimFilter();

if (LOG) {
    for (x of rtn[0]) {
        console.log(x)
    }
}

/*${return rtn}*/
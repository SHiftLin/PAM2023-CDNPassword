(function(window) {

    function installFakeRecaptcha(url) {
        if (window.grecaptcha && window.grecaptcha.___isProxy) {
            return;
        }

        const token = 'hahahahahahahahahahahahhahahaaahahahaha';
        const loaded = [];
        const coolDownTime = 1000;

        const onload = url.searchParams.get('onload');
        const render = url.searchParams.get('render');

        let prevRun = null;

        let interacted = null;

        let id = 10000;

        let callbacks = {};

        function newCallback(func) {
            callbacks[id] = func;
            return id++;
        }

        function verifyAndGetCallback(id) {
            id = id || 10000;
            if (!(id in callbacks)) {
                throw 'No reCAPTCHA clients exist.';
            } else {
                return callbacks[id];
            }

        }

        function createClickClosure(id) {
            return function onclick() {
                grecaptcha.execute(id);
            }
        }

        async function execAsync(f, args) {
            await new Promise(resolve=>setTimeout(resolve, 1));
            if (typeof f === 'string') {
                f = window[f];
            }
            f.apply(window, args);
        }

        let riggedRecaptcha = {
            ready(f) {
                if (document.readyState !== "complete") {
                    loaded.push(f);
                } else {
                    execAsync(f);
                }
            },
            execute(id) {
                const callback = verifyAndGetCallback(id);
                interacted = true;

                const timeNow = new Date();
                if (timeNow - prevRun <= coolDownTime) {
                    return;
                }
                
                prevRun = timeNow;

                if (callback) {
                    if (callback === 'v3') {
                        return new Promise((resolve)=>{
                            resolve(token);
                        }
                        );
                    } else {
                        execAsync(callback, [token]);
                    }
                }

            },
            render(el, opts) {
                if (typeof el === 'string') {
                    el = document.getElementById(el);
                }
                let dummyEle = document.createElement('textarea');
                el.appendChild(dummyEle)
                dummyEle.name = 'g-recaptcha-response';
                dummyEle.class = 'g-recaptcha-response';
                dummyEle.style = 'display: none;';
                function cbk(token) {
                    dummyEle.value = token;
                    opts.callback && execAsync(opts.callback, [token]);
                }
                let id = newCallback(cbk);
                dummyEle.id = 'g-recaptcha-response-' + id;
                if (opts.size !== 'invisible') {
                    el.addEventListener('click', createClickClosure(id));
                    el.dataset.cdnClickRequired = true;
                }
                return id;
            },
            getResponse(id) {
                verifyAndGetCallback(id);
                if (interacted) {
                    return token;
                } else {
                    return '';
                }
            },
            reset(id) {
                verifyAndGetCallback(id);
            },
            ___isProxy: true,
            ___handleAll() {
                let buttons = document.body.querySelectorAll('[data-cdn-click-required]');
                for (let i = 0; i < buttons.length; i++) {
                    buttons[i].click();
                }
            },
            ___getInThisClosure() {
                debugger;
            }

        }

        const handler = {
            get(target, name) {
                if (target[name]) {
                    return target[name];
                } else {
                    return grecaptcha;
                }
            }
        }

        const grecaptcha = new Proxy(riggedRecaptcha,handler);

        if (onload) {
            grecaptcha.ready(onload);
        }

        //     if (window.injectedRiggedRecaptchaURL) {
        //         grecaptcha.___handleURL(window.injectedRiggedRecaptchaURL);
        //     }

        Object.defineProperty(window, "grecaptcha", {
            value: grecaptcha,
        });

        function loadButtons() {
            let elems = document.getElementsByClassName('g-recaptcha');
            for (let i = 0; i < elems.length; i++) {
                grecaptcha.render(elems[i], elems[i].dataset);
            }
        }

        if (render) {
            if (render.toLowerCase() !== 'explicit') {
                // v3
                callbacks[render] = 'v3';
            }
        } else {
            // v2, v3
            grecaptcha.ready(loadButtons);

        }

        window.addEventListener('load', ()=>{
            for (let i of loaded) {
                if (typeof i === 'string') {
                    i = window[i];
                }
                i();
            }

        }
        );
    }
    /**
     * Check if the input element will install google's recaptcha 
     * and install a fake version instead
     * @param {HTMLElement} el the element to be checked
     */
    function checkAndInstallRecaptcha(el) {
        if (el.tagName.toLowerCase() === 'script') {
            let url = el.src;
            if (url) {
                url = new URL(url);
                if (url.pathname.toLowerCase().indexOf('recaptcha') !== -1) {
                    installFakeRecaptcha(url);
                    return true;
                }
            }
        }
    }

    window.addEventListener('load', ()=>{
        // load settings
        let scripts = document.getElementsByTagName('script');
        for (let i = 0; i < scripts.length; i++) {
            if (checkAndInstallRecaptcha(scripts[i])) return;
        }
        let observer = new MutationObserver(mutationList => {
            for (let mutation of mutationList) {
                let mutatedNodes = mutation.addedNodes;
                for (let i = 0; i < mutatedNodes.length; i++) {
                    if (checkAndInstallRecaptcha(mutatedNodes[i])) return;
                }
            }
        });
        observer.observe(document.head, {childList: true});
    }
    );
}
)(this);

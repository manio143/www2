function parse_cookies() {
    var cookies = {};

    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(function (c) {
            var m = c.trim().match(/(\w+)=(.*)/);
            if (m !== undefined) {
                cookies[m[1]] = decodeURIComponent(m[2]);
            }
        });
    }
    return cookies;
}

function send(method, uri, content, onSuccess, onError, setUp) {
    var req = new XMLHttpRequest();
    req.open(method, uri, true);

    if(setUp != undefined)
        setUp(req);
    req.onreadystatechange = function () {
        if (req.readyState !== 4) return;
        if (req.status >= 200 && req.status < 300) {
            alert(req.responseText);
            onSuccess(req.status, req.responseText);
            // var resp = JSON.parse(req.responseText);
            // var csrftoken = cookies.csrftoken;
            // div.innerHTML = "Imię: "+resp.imie+"<br>Nazwisko: <input type='text' id='pt' value='"+resp.nazwisko"'><input type='button' onlick='sendpost()'>";
        }
        else {
            onError(req.status, req.responseText);
        }
    };
    if (method === "POST") {
        req.send(content);
    }
    else {
        req.send();
    }
    return req;
}


function displaySearchBox() {
    alert("search");

    return false;
}

function setVisibility(id, visible) {
    document.getElementById(id).style.display = visible ? "inherit" : "none";
}

function setStats(stats) {
    var uprawnieni = document.getElementById("stats.uprawnieni");
    var wydane = document.getElementById("stats.wydane");
    var oddane = document.getElementById("stats.oddane");
    var wazne = document.getElementById("stats.wazne");
    var niewazne = document.getElementById("stats.niewazne");
    var frekwencja = document.getElementById("stats.frekwencja");

    uprawnieni.innerHTML = stats.uprawnieni;
    wydane.innerHTML = stats.wydane;
    oddane.innerHTML = stats.oddane;
    wazne.innerHTML = stats.wazne;
    niewazne.innerHTML = stats.niewazne;
    frekwencja.innerHTML = stats.frekwencja;
}

function setResult(resultTable, result) {
    var body = resultTable.getElementsByTagName("tbody")[0];
    var rows = body.getElementsByTagName("tr");
    for (let index = 0; index < rows.length; index++) {
        rows[index].children[0].innerHTML = result[index].nazwa;
        rows[index].children[1].innerHTML = result[index].glosy;
        var bar = rows[index].children[2].getElementsByClassName("votebar")[0];
        var freq = rows[index].children[2].getElementsByTagName("span")[0];
        bar.style.width = result[index].procent + "%";
        freq.innerHTML = result[index].procent + "%";
    }
}

function setMainResult(result) {
    var mainResult = document.getElementById("mainResult");
    setResult(mainResult, result);
}

function setResults(results) {
    var mainResult = document.getElementById("mainResult");
    var resultsWrapper = document.getElementById("results-wrapper");
    for (let i = 0; i < results.length; i++) {
        var newResult = mainResult.cloneNode(true);
        newResult.id = undefined;
        newResult.setAttribute("name", "results");
        newResult.dataset.id = i;
        setResult(newResult, results[i].result);
        resultsWrapper.appendChild(newResult);
    }
}

function setMore(links) {
    var more = document.getElementById("more");
    for (child of more.children)
        more.removeChild(child);
    for (let i = 0; i < links.length; i++) {
        let div = document.createElement('div');
        div.classList.add("col-3");

        let a = document.createElement('a');
        a.href = links[i].url;
        a.innerHTML = links[i].nazwa;

        div.appendChild(a);
        more.appendChild(div);
    }
}

function deleteResults() {
    var results = document.getElementsByName("results");
    if (results.length > 0) {
        var parent = results[0].parentElement;
        for (result of results)
            parent.removeChild(result);
    }
}

function buildFromData(data) {
    setStats(data.stats);
    setMainResult(data.mainResult);
    if (data.type === "main") {
        setVisibility("map", true);
        setVisibility("more-wrapper", false);
    } else if (data.type === "details") {
        setVisibility("map", false);
        setVisibility("more-wrapper", true);
        setMore(data.more.links);
    } else if (data.type === "gmina") {
        setVisibility("map", false);
        setVisibility("more-wrapper", false);
        setMainResult(data.mainResult);
        setResults(data.more.results);
    }
}

function onError(status, resp) {
    alert("Request returned " + status + "\n" + resp);
}

function makeRedirect(href) {
    return () => {
        function processResponse(status, response) {
            var resp = JSON.parse(response);
            var prevUri = location.hash;

            location.hash = href;

            deleteResults();

            buildFromData(resp);

            saveLocalData(resp);

            setAnchors();
        }

        send("GET", href, {}, processResponse, onError);

        return false;
    }
}

function popupLogin() {
    let req = send("GET", "/login", {}, (status, view) => {
        setVisibility("popup-wrapper", true);
        setVisibility("popup-login", true);
        setVisibility("popup-search", false);

        let popupLogin = document.getElementById("popup-login");
        popupLogin.innerHTML = view;

        let form = document.getElementById("form-login");
        form.submit = (e) => {            
            var params = new FormData(form)
            var csrf = form.elements.csrfmiddlewaretoken.value;
            send("POST", "/login", params, () => {
                var login = document.getElementById("login");
                login.setAttribute("id", "login");
                login.innerText = "Logout";
                setAuthLinks();
                resetContent();
            }, onError, (req) => {
                req.setRequestHeader("Content-type", "application/json");
                req.setRequestHeader("X-Csrf-Token", csrf);
            });

            return false;
        }

        return false;
    }, onError);
}

function setAnchors() {
    var anchors = document.getElementsByTagName("a");
    for (anchor of anchors) {
        if (anchor.getAttributeNS('http://www.w3.org/1999/xlink', 'href'))
            anchor.onclick = makeRedirect(anchor.getAttributeNS('http://www.w3.org/1999/xlink', 'href'))
        else if (anchor.href != location.origin + location.pathname + "#") {
            anchor.onclick = makeRedirect(anchor.href);
        }
    }
}

function saveLocalData(data) {
    localStorage.setItem("data", JSON.stringify(data));
}

function loadLocalData() {
    var data = JSON.parse(localStorage.getItem("data"));

    deleteResults();

    buildFromData(data);

    setAnchors();
}

function loadIndex() {
    makeRedirect("/index")();
}

function localDataAvailable() {
    return localStorage.getItem("data") != null;
}

function setAuthLinks() {
    var login = document.getElementById("login");
    if (login == undefined) {
        var logout = document.getElementById("logout");
        logout.onclick = () => {
            send("GET", "/logout", {}, () => {
                logout.setAttribute("id", "login");
                logout.innerText = "Login";
                setAuthLinks();
                resetContent();
            }, onError);
            return false;
        }
    } else {
        login.onclick = () => {
            popupLogin();
            return false;
        }
    }
}

function resetContent() {
    makeRedirect(location.hash)();
}

window.onload = function () {
    var search = document.getElementById("search_btn");
    search.onclick = displaySearchBox;

    setAuthLinks();

    if (localDataAvailable())
        loadLocalData();

    loadIndex();
};

/*
    TODO: search, login, edit, link to index

    known bugs: object stays after change (possibly can't remove 'this')
*/
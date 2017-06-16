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

    if (setUp !== undefined)
        setUp(req);
    req.onreadystatechange = function () {
        if (req.readyState !== 4) return;
        if (req.status >= 200 && req.status < 300) {
            //alert(req.responseText);
            onSuccess(req.status, req.responseText);
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

function parseform(form) {
    var formData = new FormData(form);
    var obj = {};
    for(var pair of formData.entries())
        obj[pair[0]] = pair[1];
    return JSON.stringify(obj);
}

function clearChildren(node) {
    while (node.hasChildNodes()) {
        node.removeChild(node.lastChild);
    }
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

function setResult(resultTable, result, auth) {
    var body = resultTable.getElementsByTagName("tbody")[0];
    if (auth)
        resultTable.getElementsByTagName("th")[3].style.visibility = "visible";
    var rows = body.getElementsByTagName("tr");
    if(rows.length > result.length) {
        for(let i = 0; i<rows.length - result.length; i++)
            body.removeChild(body.lastChild);
    }
    rows = body.getElementsByTagName("tr");    
    for (let index = 0; index < result.length; index++) {
        if(rows.length <= index) {
            body.appendChild(rows[index-1].cloneNode(true));
            rows = body.getElementsByTagName("tr");
        }
        rows[index].children[0].innerHTML = result[index].nazwa;
        rows[index].children[1].innerHTML = result[index].glosy;
        var bar = rows[index].children[2].getElementsByClassName("votebar")[0];
        var freq = rows[index].children[2].getElementsByTagName("span")[0];
        bar.style.width = result[index].procent + "%";
        freq.innerHTML = result[index].procent + "%";
        if (auth) {
            rows[index].children[3].style.visibility = "visible";
            rows[index].children[3].innerHTML = "<a href=\"#\" onclick=\"return editScore.apply(this);\" data-id=\"" + (index + 1) + "\">Edytuj</a>";
        }
    }
}

function setMainResult(result) {
    var mainResult = document.getElementById("mainResult");
    setResult(mainResult, result);
}

function setResults(results, auth) {
    var mainResult = document.getElementById("mainResult");
    var resultsWrapper = document.getElementById("results-wrapper");
    for (let i = 0; i < results.length; i++) {
        var newResult = mainResult.cloneNode(true);
        newResult.removeAttribute("id");
        newResult.setAttribute("name", "results");
        newResult.dataset.id = results[i].id;
        setResult(newResult, results[i].result, auth);
        resultsWrapper.appendChild(newResult);
    }
}

function setMore(links) {
    var more = document.getElementById("more");
    clearChildren(more);
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
    while (document.getElementsByName("results").length > 0) {
        var resultsWrapper = document.getElementById("results-wrapper");
        clearChildren(resultsWrapper);
    }
    // var results = document.getElementsByName("results");
    // if (results.length > 0) {
    //     var parent = results[0].parentElement;
    //     for (result of results)
    //         parent.removeChild(result);
    // }
}

function buildFromData(data) {
    currentData = data;
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
        setResults(data.more.results, data.auth);
    }
}

function onError(status, resp) {
    alert("Request returned " + status + "\n" + resp);
}

function makeRedirect(href) {
    href = href.replace(location.origin + location.pathname, "");
    return () => {
        function processResponse(status, response) {
            var resp;
            try {
                resp = JSON.parse(response);
            } catch (err) {
                alert(err + "\n" + response);
                throw err;
            }

            location.hash = href;

            deleteResults();

            buildFromData(resp);

            saveLocalData(resp);

            setAnchors();
        }

        if (fromSearch) {
            setVisibility("popup-wrapper", false); //hide searchbox
            fromSearch = false;
        }
        send("GET", href, {}, processResponse, onError);

        return false;
    };
}

var fromSearch = false;

function displaySearchBox() {
    setVisibility("popup-wrapper", true);
    setVisibility("popup-login", false);
    setVisibility("popup-search", true);
    setVisibility("popup-edit", false);

    let form = document.getElementById("search-form");
    form.onsubmit = form.submit = searchSubmit;

    fromSearch = true;

    return false;
}

function searchSubmit() {
    let params = new FormData(this);
    let q = params.get("q");
    send("GET", "/search?q=" + q, {}, (s, _data) => {
        let searchResults = document.getElementById("search-results");
        clearChildren(searchResults);
        let data = JSON.parse(_data);
        for (var g of data.gminy) {
            let a = document.createElement('a');
            a.href = "/gmina/" + g.nazwa + "-" + g.id;
            a.innerHTML = g.nazwa;
            searchResults.appendChild(a);
            searchResults.appendChild(document.createElement("br"));
        }

        setAnchors();
    }, onError);

    return false;
}

var currentData;

function validate_edit(newVal, id, candidateId) {
    var data = currentData.more.results.filter(x => x.id == id)[0];
    var sum_oddane = data.result.map(x => x.glosy).reduce((acc, val) => acc + val, 0) - data.result[candidateId - 1].glosy + Number(newVal);
    return sum_oddane <= data.max;
}

function editScore() {
    let row = this.parentElement.parentElement;
    let table = row.parentElement.parentElement;
    let id = table.parentElement.dataset.id;
    let candidateId = this.dataset.id;

    setVisibility("popup-wrapper", true);
    setVisibility("popup-login", false);
    setVisibility("popup-search", false);
    setVisibility("popup-edit", true);

    let err = document.getElementById("edit-form-err");
    let suc = document.getElementById("edit-form-succ");
    err.innerHTML = "";
    suc.innerHTML = "";

    let form = document.getElementById("edit-form");
    let scoreInput = document.getElementById("id_oddane");
    scoreInput.value = row.getElementsByClassName("data-glosy")[0].innerText;
    form.onsubmit = form.submit = () => {
        var params = parseform(form);
        if (validate_edit(form.elements.oddane.value, id, candidateId)) {
            var csrf = parse_cookies().csrftoken;
            send("POST", "/edit/" + id + "/" + candidateId, params, (status, response) => {
                let data = JSON.parse(response);
                err.innerHTML = "";
                suc.innerHTML = "";
                if (data.success !== null) {
                    suc.innerHTML = data.success;
                    resetContent();
                } else {
                    err.innerHTML = data.error;
                }
            }, onError, (req) => {
                req.setRequestHeader("X-CSRFToken", csrf);
            });
        } else {
            suc.innerHTML = "";
            err.innerHTML = "Liczba głosów oddanych w obwodzie nie może przekraczać liczby wydanych kart.";
        }
        return false;
    };

    return false;
}

function popupLogin() {
    setVisibility("popup-wrapper", true);
    setVisibility("popup-login", true);
    setVisibility("popup-search", false);
    setVisibility("popup-edit", false);

    let err = document.getElementById("login-form-err");
    err.innerHTML = "";

    let form = document.getElementById("form-login");
    form.onsubmit = form.submit = () => {
        var params = parseform(form);
        var csrf = parse_cookies().csrftoken;
        send("POST", "/login", params, () => {
            var login = document.getElementById("login");
            login.setAttribute("id", "logout");
            login.innerText = "Logout";
            setVisibility("popup-wrapper", false);
            setAuthLinks();
            resetContent();
        }, (status, response) => {
            if (status == 420) {
                err.innerHTML = JSON.parse(response).error;
                form.elements.password.value = "";
            }
            else onError(status, response);
        }, (req) => {
            req.setRequestHeader("X-CSRFToken", csrf);
        });

        return false;
    };
}
function setAnchors() {
    var anchors = document.getElementsByTagName("a");
    for (var i=0; i<anchors.length; i++) {
        var anchor = anchors[i];
        if (anchor.getAttributeNS('http://www.w3.org/1999/xlink', 'href'))
            anchor.onclick = makeRedirect(anchor.getAttributeNS('http://www.w3.org/1999/xlink', 'href'));
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
    return localStorage.getItem("data") !== null;
}

function setAuthLinks() {
    var login = document.getElementById("login");
    if (login === null) {
        var logout = document.getElementById("logout");
        logout.onclick = () => {
            send("GET", "/logout", {}, () => {
                logout.setAttribute("id", "login");
                logout.innerText = "Login";
                setAuthLinks();
                resetContent();
            }, onError);
            return false;
        };
    } else {
        login.onclick = () => {
            popupLogin();
            return false;
        };
    }
}

function currentLocation() {
    return location.hash.replace("#", "");
}

function resetContent() {
    makeRedirect(currentLocation())();
}

window.onload = function () {
    var search = document.getElementById("search_btn");
    search.onclick = displaySearchBox;

    setAuthLinks();

    if (localDataAvailable())
        loadLocalData();

    loadIndex();
};

function loadExternalElement(url, targetId, onLoad){
    var template = document.createElement('template');
    var target = document.getElementById(targetId);
    fetch(url).then(response => {
        return response.text()
    }).then(html => {
        template.innerHTML = html;
        var element = template.content.firstElementChild;
        element.id = targetId;
        target.replaceWith(element);
    }).then(onLoad);
}

var query = window.location.search;
var params = new URLSearchParams(query);
AUTHORIZATION_KEY = params.get("AUTH-KEY");
// function ChangeUrl(title, url) {
//     if (typeof (history.pushState) != "undefined") {
//         var obj = { Title: title, Url: url };
//         history.pushState(obj, obj.Title, obj.Url);
//     } else {
//         console.log('url rewriting will not work')
//     }
// }

function syntaxHighlight(input) {
    input = input.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return input.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            var cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return $("<span/>", {"class": cls}).text(match);
        });
}


$('#results').hide()

function do_search(attr, val) {
    url = '/' + attr + '/' + val
    backend= '/rest/v1'+url
    // ChangeUrl('search',url)
    $.ajax({
        url: backend,
        type: "GET",
        dataType: "json",
        success: function (data) {
            // console.log(JSON.stringify(data)));
            // console.log(JSON.stringify(data));
            $('#results').append(JSON.stringify(data,undefined,4))
            $('#results').show()
            $([document.documentElement, document.body]).animate({scrollTop: $("#results").offset().top}, 2000);
        },
        error: function (error) {
            console.log(`Error ${error}`);
        }
    });
};
// var pathname = window.location.pathname;
// if (pathname.includes('/id/')){
//     do_search('id',pathname.replace('/rest/v1/id/'),"")
// }else if (pathname.includes('/name/')){
//     do_search('name',pathname.replace('/rest/v1/name/'),"")
// }else if (pathname.includes('/standard/')){
//     do_search('standard',pathname.replace('/rest/v1/standard/'),"")
// }

$('#CREsearchBtn').click(function () {
    switch ($('#CREsearchDropdown').val()) {
        case 'id':
            do_search('id', $('#CRESearchInput').val())
            break;
        case 'name':
            do_search('name', $('#CRESearchInput').val())
            break;
        case 'standard':
            do_search('standard', $('#CRESearchInput').val())
            break;
    }
})
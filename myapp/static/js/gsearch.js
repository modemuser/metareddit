
google.load('search', '1');
google.setOnLoadCallback(OnLoad);

var webSearch, perma_link, reddit_link, google_link;

function addPaginationLinks() {
    // The cursor object has all things to do with pagination
    var cursor = webSearch.cursor;
    var pagesDiv = document.createElement('div');
    pagesDiv.setAttribute('class', 'pagination');
    pagesDiv.appendChild(document.createTextNode('view more: '));
    // check what page the app is on
    var curPage = cursor.currentPageIndex;
    var nextPage, prevPage;
    if (curPage < cursor.pages.length-1) {
        nextPage = curPage + 1;
    }
    if (curPage !== 0) {
        prevPage = curPage - 1;
    }
    if (nextPage != null || prevPage != null) {
        //make prev link
        if (prevPage != null) {
            var prevLink = document.createElement('a');
            prevLink.href = 'javascript:webSearch.gotoPage('+prevPage+');';
            prevLink.setAttribute('class', 'page');
            prevLink.innerHTML = 'prev';
            prevLink.style.marginRight = '5px';
            pagesDiv.appendChild(prevLink);
        }
        // divider
        if (nextPage != null && prevPage != null) {
            pagesDiv.appendChild(document.createTextNode('| '));
        }
        //make next link
        if (nextPage != null) {
            var nextLink = document.createElement('a');
            nextLink.href = 'javascript:webSearch.gotoPage('+nextPage+');';
            nextLink.setAttribute('class', 'page');
            nextLink.innerHTML = 'next';
            pagesDiv.appendChild(nextLink);
        }
        var contentDiv = document.getElementById('gsearch_result');
        contentDiv.appendChild(pagesDiv);
    }
}

function searchComplete() {
    var contentDiv = document.getElementById('gsearch_result');
    // Grab our content div, clear it.
    contentDiv.innerHTML = '<div id="gsearch_branding"></div><div id="choice">'
            + '<a href="' + perma_link + '">permalink</a> | this search on: '
            + '<a href="' + reddit_link + '">reddit</a> | ' 
            + '<a href="' + google_link + '">google</a>' 
            + '</div>';
    // Check that we got results
    if (webSearch.results && webSearch.results.length > 0) {
        // Loop through our results, printing them to the page.
        var results = webSearch.results;
        for (var i = 0; i < results.length; i++) {
            var result = results[i];
            var container = document.createElement('div');
            container.setAttribute('class', 'submission');

            var title = document.createElement('a');
            title.setAttribute('class', 'title');
            var url = result.unescapedUrl;
            if (url.match('.mobile$') == '.mobile') {
                url = url.substr(0, url.length - 7);
            }
            title.setAttribute('href', url);
            title.innerHTML = result.titleNoFormatting;

            var domain = document.createElement('span');
            domain.setAttribute('class', 'domain');
            domain.innerHTML = '/' + url.split('/').slice(3).join('/');

            var tagline = document.createElement('div');
            tagline.innerHTML = result.content;
            
            container.appendChild(title);
            container.appendChild(tagline);
            container.appendChild(domain);

            contentDiv.appendChild(container);
        }

        // Now add the paging links so the user can see more results.
        addPaginationLinks(webSearch);
    }
    else {
        contentDiv.innerHTML += '<p>Nothing found.</p>';
    }
}


function OnLoad() {
    webSearch = new google.search.WebSearch();
    webSearch.setResultSetSize(google.search.Search.LARGE_RESULTSET);
    webSearch.setSearchCompleteCallback(this, searchComplete, null);
    var qs = window.location.search.substring(1);
    if (qs.length != 0) {
        var q, r;
        var parts = qs.split('&');
        for (var i = 0; i < parts.length; i++) {
            var tuple = parts[i].split('=');
            if (tuple[0] == 'q') {
                q = unescape(tuple[1]);
                document.getElementById('gsearch_term').value = q;
            } 
            else if (tuple[0] == 'r') {
                r = tuple[1];
                document.getElementById('gsearch_reddits').value = r;
            }
        }
        _search(q, r);
        return false;
    }
}


function gsearch() {
    var query = document.getElementById('gsearch_term').value;
    if (query.length == 0) {
        return false;
    }
    var contentDiv = document.getElementById('gsearch_result');
    contentDiv.innerHTML = 'loading...';
    var reddits = document.getElementById('gsearch_reddits').value;
    _search(query, reddits);
    return false;
}


function _search(query, reddits) {
    if (query.length == 0) {
        return false;
    }
    reddits_clean = '';
    var sites = 'www.reddit.com';
    reddit_link = 'http://www.reddit.com/r/'
    if (reddits != null && reddits.length != 0) {
        sites = ''
        var r = reddits.split('+');
        for (var i = 0; i < r.length; i++) {
            if (r[i].length == '') {
                continue;
            }
            if (i > 0) {
                sites += 'site:';
            }
            sites += 'www.reddit.com/r/' + r[i] + '/comments/ OR ';
            reddits_clean += r[i] + '+';
        }
        //remove last OR
        sites = sites.slice(0, sites.length-4);
        reddits_clean = reddits_clean.slice(0, reddits_clean.length-1);
        reddit_link += reddits_clean;
    }
    else {
        reddit_link += 'all';
    }
    webSearch.setSiteRestriction(sites);
    var filter = '-inurl:(/shirt/|/related/|/domain/|/new/|/top/|/controversial/|/widget/|/buttons/|/about/|/duplicates/|sort=|dest=|/i18n)';
    webSearch.setQueryAddition(filter);
    perma_link = '/search?q=' + escape(query) + '&r=' + reddits_clean
    reddit_link += '/search?q=' + escape(query)
    google_link = 'http://www.google.com/search?q=' + escape(query) + '+site:' +    sites + '+' + filter + '&num=50'
    webSearch.execute(query);
}



from myapp.config import admins
from myapp.lib.memoize import memoize
from myapp.lib.utils import url_for, render_template


def header(username=None):
    if username is None:
        return """want to join? <a href="%s" class="loginbutton">register</a> in seconds""" % url_for('login')
    else:
        if username not in admins:
            return """<a href="%s">%s</a> | <a href="%s">log out</a>""" \
                    % (url_for('user', username=username), username.encode('ascii'), url_for('logout'))
        else:
            return """<a href="%s">%s</a> | <a href="%s">admin</a> | <a href="%s">log out</a>"""\
                    % (url_for('user', username=username), username.encode('ascii'), url_for('admin'), url_for('logout'))


@memoize('view_placeholder_highlight')
def highlight(endpoint): 
    if endpoint == 'index':
        s = """\
            <p>
                metareddit is all about <a href="http://www.reddit.com">reddit.com</a> and its many (sub-)reddits. 
                You can explore the <a href="%s">reddits</a>, 
                similar ones can be grouped using <a href="%s">tags</a>.
                Once you <a class="loginbutton" href="%s">register</a>,
                you can add tags too, and vote them up or down, depending on whether they fit the reddit.
            </p>
            <p>
                See the <a href="%s">help page</a> for more information on the features.
            </p>
        """ % (url_for('reddits'), url_for('tags'), url_for('login'), url_for('help'))
    elif endpoint == 'reddits':
        s = """\
            explore reddits: bigger means more subscribers, darker means more recent submissions.
        """
    elif endpoint == 'tags':
        s ="""\
            group reddits: tags let you find, browse, search, bundle reddits that share a common subject.
        """
    elif endpoint == 'search':
        s = """\
            search in all of reddit.com, or only in the submissions and comments of chosen subreddits.
        """
    elif endpoint == 'stalk':
        s = """\
            find out in which subreddits a redditor is active by scanning their recent activity
        """
    elif endpoint == 'monitor':
        s = """\
            monitor all new comments, submission titles and self-texts posted to reddit for a word or phrase. If you're logged in, see your userpage for a summary of things you're monitoring.
        """
    elif endpoint == 'logos':
        s = """\
            some reddits have custom logos. Here you can browse the logos of the biggest couple of thousand reddits.
        """
    else:
        return ''
    return """<div id="highlight">%s</div>""" % s


def popup():
    return render_template('popup.html').encode('ascii')



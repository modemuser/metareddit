from contrib.jsmin import JavascriptMinify
    
path = '/home/www/vhost/metareddit/myapp/static/js/'
files = [
    'jquery.cookie.js',
    'jquery.scrollTo.js',
    'jquery.simplemodal.js',
    'jquery.autocomplete.js',
    'script.js',
]

def minify(path, filename):
    print 'minifiying: ' + filename
    jsm = JavascriptMinify()
    file = open(path + filename, 'r')
    out = open(path + filename[:-2] + 'min.js', 'w')
    jsm.minify(file, out)
    out.close()


def combine(path, files, newname):
    jsm = JavascriptMinify()
    out = open(path + newname, 'w')
    for f in files:
        print 'minifying: ' + f
        file = open(path + f, 'r')
        jsm.minify(file, out)
    print 'saved as', newname
    out.close()


def main():
    combine(path, files, 'metareddit.js')
    combine(path, ['gsearch.js'], 'gsearch.min.js')


if __name__ == '__main__':
    main()

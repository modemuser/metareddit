from werkzeug import redirect
from werkzeug.exceptions import Forbidden
from myapp.env import session
from myapp.models import User
from myapp.lib.auth import cookie_expires, cookie_lifespan, is_valid_token
from myapp.lib.utils import url_for, serve_response
from myapp.lib.db.queries import get_user


def login(request):
    response = None
    if request.method == 'POST':
        token = request.form.get('token')
        todo = request.form.get('do')
        if not is_valid_token(todo, token):
            raise Forbidden
        if todo == 'login':
            response = login_form(request)
        if todo == 'reg':
            response = register_form(request)
    if not response:
        response = serve_response('login.html')
    request.session.save_cookie(response, expires=cookie_expires(), max_age=cookie_lifespan())
    return response


def login_form(request):
    username = request.form.get('username')
    password = request.form.get('passwd')
    user = get_user(username)
    if user and user.is_valid_pw(password):
        request.login(username)
        return redirect(url_for('index'))
    flashMsg = 'Invalid credentials.'
    return serve_response('login.html', flashMsg=flashMsg)


def register_form(request):
    # getting and checking input
    username = request.form.get('username', None)
    pw1 = request.form.get('passwd', None)
    pw2 = request.form.get('passwd2', None)
    if not (username and pw1 and pw2):
        return serve_response('login.html', flashMsg='All fields are required.')
    if ' ' in username:
        return serve_response('login.html', flashMsg='Username cannot contain spaces.')
    if get_user(username):
        return serve_response('login.html', flashMsg='Username exists! Please choose another username.')
    if pw1 != pw2:
        return serve_response('login.html', flashMsg='Passwords don\'t match.')
    # create user
    user = User(username, pw1)
    session.commit()
    return login_form(request)


def logout(request):
    request.logout()
    response =  redirect(url_for('index'))
    request.session.save_cookie(response, expires=0, max_age=0)
    return response


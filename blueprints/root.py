import app
import flask

page = flask.Blueprint('root', __name__)
require_login = app.hooks.require_login

@page.route('/')
@require_login
def index():
    return flask.render_template('root/index.html')
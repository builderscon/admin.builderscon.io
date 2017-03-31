import app
import flask
import functools
import time
import uuid

page = flask.Blueprint('venue', __name__)
COLUMNS = [
    'name',
    'address',
    'name#ja',
    'address#ja',
    'latitude',
    'longitude'
]
REQUIRED = {
    'name': True,
    'address': True,
    'latitude': True,
    'longitude': True
}

with_venue = app.hooks.with_venue
require_login = app.hooks.require_login

@page.route('/venue/')
@require_login
def list():
    return flask.render_template('venue/index.html')

@page.route('/venue/<id>/view')
@require_login
@functools.partial(with_venue, lang='all')
def view():
    return flask.render_template('venue/view.html')

@page.route('/venue/input', methods=['GET'])
@require_login
def input():
    return flask.render_template('venue/input.html')

@page.route('/venue/input', methods=['POST'])
@require_login
def input_post():
    # For this action, merge the new values withe conference
    # object, so that we can show the user the edits
    v = {}
    for k in COLUMNS:
        if k not in flask.request.values:
            continue
        if flask.request.values[k] is None:
            continue
        v[k] = flask.request.values[k]

    errors = []
    for k in REQUIRED:
        if k not in v or v[k] == '':
            errors.append({'error': 'missing', 'field': k})

    if len(errors) > 0:
        flask.g.stash['errors'] = errors
        flask.g.stash['venue'] = v
        return flask.render_template('venue/input.html')

    for k in ['latitude', 'longitude']:
        v[k] = float(v[k])

    flask.g.stash['venue'] = v
    subs = str(uuid.uuid4())
    subskey = 'venue.create'
    if subskey not in flask.session:
        flask.session[subskey] = {}
    now = time.time()
    flask.session[subskey][subs] = {
        'expires': now + 900,
        'data': v
    }
    keys = flask.session[subskey].keys()
    for k in keys:
        if flask.session[subskey][k]['expires'] < now:
            print('Deleting subsession %s' % k)
            del flask.session[subskey][k]
    flask.g.stash['subsession'] = subs
    return flask.render_template('venue/confirm.html')


@page.route('/venue/create', methods=['POST'])
@require_login
def create():
    subskey = 'venue.create'
    if subskey not in flask.session:
        print('no %s' % subskey)
        return flask.abort(500)

    subs = flask.request.values.get('subsession')
    if not subs:
        print('no %s' % subs)
        return flask.abort(500)
    subs = subs.encode('ascii')

    if subs not in flask.session[subskey]:
        print('no %s in subsession container' % subs)
        return flask.abort(500)

    v = flask.session[subskey][subs]
    if not v:
        return flask.abort(500)

    datakey = 'data'
    if datakey not in v:
        return flask.abort(500)

    data = v[datakey]
    data['user_id'] = flask.session['user_id']
    new_venue = flask.g.api.create_venue(**data)
    if not new_venue:
        flask.g.stash['errors'] = [{'error': flask.g.api.last_error()}]
        return flask.render_template('venue/input.html')

    del flask.session[subskey][subs]
    flask.g.stash['venue'] = new_venue
    return flask.render_template('venue/create.html')

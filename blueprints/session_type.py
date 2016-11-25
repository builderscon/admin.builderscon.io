import app
import flask
import functools
import time
import uuid

page = flask.Blueprint('session_type', __name__)
COLUMNS = [
    'abstract',
    'abstract#ja',
    'name',
    'name#ja',
    'duration',
    'is_default',
    'submission_start',
    'submission_end'
]
REQUIRED = {
    'name': True,
    'abstract': True,
    'duration': True
}

with_session_type = app.hooks.with_session_type
with_associated_conference = app.hooks.with_associated_conference

@page.route('/session_type/<id>/view')
@functools.partial(with_session_type, lang='all')
@functools.partial(with_associated_conference, id_getter=lambda: flask.g.stash.get('session_type').get('conference_id'))
def view():
    print("view")
    return flask.render_template('session_type/view.html')

@page.route('/session_type/input', methods=['GET'])
def input():
    return flask.render_template('session_type/input.html')

@page.route('/session_type/input', methods=['POST'])
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
        flask.g.stash['session_type'] = v
        return flask.render_template('session_type/input.html')

    for k in ['latitude', 'longitude']:
        v[k] = float(v[k])

    flask.g.stash['session_type'] = v
    subs = str(uuid.uuid4())
    subskey = 'session_type.create'
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
    return flask.render_template('session_type/confirm.html')


@page.route('/session_type/create', methods=['POST'])
def create():
    subskey = 'session_type.create'
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
    new_session_type = app.api.create_session_type(**data)
    if not new_session_type:
        flask.g.stash['errors'] = [{'error': app.api.last_error()}]
        return flask.render_template('session_type/input.html')

    del flask.session[subskey][subs]
    flask.g.stash['session_type'] = new_session_type
    return flask.render_template('session_type/create.html')

@page.route('/session_type/<id>/edit', methods=['POST'])
@functools.partial(with_session_type, lang='all')
def edit():
    # For this action, merge the new values withe session_type
    # object, so that we can show the user the edits
    v = {}
    for k in COLUMNS:
        if k not in flask.request.values:
            continue
        if flask.request.values[k] is None:
            continue
        v[k] = flask.request.values[k]
        if k == 'is_default' and v[k]:
            v[k] = True
        elif k == 'duration' and v[k]:
            v[k] = int(v[k])

    c = flask.g.stash.get('session_type')
    h = {}
    for k in COLUMNS:
        if k in v:
            h[k] = v[k]
        elif k in c and c[k] is not None:
            h[k] = c[k]
    flask.g.stash['new_session_type'] = h

    subs = str(uuid.uuid4())
    subskey = 'session_type.edit'
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
    return flask.render_template('session_type/edit.html')

@page.route('/session_type/<id>/update', methods=['POST'])
@functools.partial(with_session_type, lang='all')
def update():
    subskey = 'session_type.edit'
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
    data['id'] = flask.g.stash.get('session_type_id')
    data['user_id'] = flask.session['user_id']
    ok = app.api.update_session_type(**data)
    if not ok:
        flask.g.stash['error'] = app.api.last_error()

    del flask.session[subskey][subs]
    return flask.render_template('session_type/update.html')

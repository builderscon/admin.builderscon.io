import app
import flask
import functools
import time
import uuid

page = flask.Blueprint('sponsor', __name__)
COLUMNS = [
    'conference_id',
    'logo_url',
    'url',
    'name#ja',
    'name',
    'group_name',
    'sort_order'
]
REQUIRED = {
    'conference_id': True,
    'name': True,
    'url': True
}

with_sponsor = app.hooks.with_sponsor
with_associated_conference = app.hooks.with_associated_conference

@page.route('/sponsor/<id>/view')
@functools.partial(with_sponsor, lang='all')
@functools.partial(with_associated_conference, id_getter=lambda: flask.g.stash.get('sponsor').get('conference_id'))
def view():
    return flask.render_template('sponsor/view.html')

@page.route('/sponsor/input', methods=['GET'])
def input():
    return flask.render_template('sponsor/input.html')

@page.route('/sponsor/input', methods=['POST'])
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
        flask.g.stash['sponsor'] = v
        return flask.render_template('sponsor/input.html')

    for k in ['latitude', 'longitude']:
        v[k] = float(v[k])

    flask.g.stash['sponsor'] = v
    subs = str(uuid.uuid4())
    subskey = 'sponsor.create'
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
    return flask.render_template('sponsor/confirm.html')


@page.route('/sponsor/create', methods=['POST'])
def create():
    subskey = 'sponsor.create'
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
    new_sponsor = app.api.create_sponsor(**data)
    if not new_sponsor:
        flask.g.stash['errors'] = [{'error': app.api.last_error()}]
        return flask.render_template('sponsor/input.html')

    del flask.session[subskey][subs]
    flask.g.stash['sponsor'] = new_sponsor
    return flask.render_template('sponsor/create.html')

@page.route('/sponsor/<id>/edit', methods=['POST'])
@functools.partial(with_sponsor, lang='all')
def edit():
    # For this action, merge the new values withe sponsor
    # object, so that we can show the user the edits
    v = {}
    print(flask.request.values)
    for k in COLUMNS:
        print(k)
        if k not in flask.request.values:
            continue
        if flask.request.values[k] is None:
            continue
        v[k] = flask.request.values[k]
    print(v)

    c = flask.g.stash.get('sponsor')
    h = {}
    for k in COLUMNS:
        if k in v:
            h[k] = v[k]
        elif k in c and c[k] is not None:
            h[k] = c[k]
    flask.g.stash['new_sponsor'] = h

    subs = str(uuid.uuid4())
    subskey = 'sponsor.edit'
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
    return flask.render_template('sponsor/edit.html')

@page.route('/sponsor/<id>/update', methods=['POST'])
@functools.partial(with_sponsor, lang='all')
def update():
    subskey = 'sponsor.edit'
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
    data['id'] = flask.g.stash.get('sponsor_id')
    data['user_id'] = flask.session['user_id']
    ok = app.api.update_sponsor(**data)
    if not ok:
        flask.g.stash['error'] = app.api.last_error()

    del flask.session[subskey][subs]
    return flask.render_template('sponsor/update.html')

import app
import flask
import functools
import time
import uuid

page = flask.Blueprint('blog_entry', __name__)
COLUMNS = [
    'url',
    'title',
    'status',
    'image_url',
    'conference_id'
]
REQUIRED = {
    'url': True,
    'title': True,
    'status': True,
    'image_url': True,
    'conference_id': True
}

with_blog_entry = app.hooks.with_blog_entry
with_associated_conference = app.hooks.with_associated_conference
require_login = app.hooks.require_login

@page.route('/blog_entry/<id>/view')
@require_login
@functools.partial(with_blog_entry, lang='all')
@functools.partial(with_associated_conference, id_getter=lambda: flask.g.stash.get('blog_entry').get('conference_id'))
def view():
    print("view")
    return flask.render_template('blog_entry/view.html')

@page.route('/blog_entry/input', methods=['GET'])
@require_login
def input():
    return flask.render_template('blog_entry/input.html')

@page.route('/blog_entry/input', methods=['POST'])
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
        flask.g.stash['blog_entry'] = v
        return flask.render_template('blog_entry/input.html')

    flask.g.stash['blog_entry'] = v
    subs = str(uuid.uuid4())
    subskey = 'blog_entry.create'
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
    return flask.render_template('blog_entry/confirm.html')


@page.route('/blog_entry/create', methods=['POST'])
@require_login
def create():
    subskey = 'blog_entry.create'
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
    flask.g.stash['conference_id'] = data['conference_id'] # for form
    new_blog_entry = flask.g.api.create_blog_entry(**data)
    if not new_blog_entry:
        flask.g.stash['errors'] = [{'error': flask.g.api.last_error()}]
        return flask.render_template('blog_entry/input.html')

    del flask.session[subskey][subs]
    flask.g.stash['blog_entry'] = new_blog_entry
    return flask.render_template('blog_entry/create.html')

@page.route('/blog_entry/<id>/edit', methods=['POST'])
@require_login
@functools.partial(with_blog_entry, lang='all')
def edit():
    # For this action, merge the new values withe blog_entry
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

    c = flask.g.stash.get('blog_entry')
    h = {}
    for k in COLUMNS:
        if k in v:
            h[k] = v[k]
        elif k in c and c[k] is not None:
            h[k] = c[k]
    flask.g.stash['new_blog_entry'] = h

    subs = str(uuid.uuid4())
    subskey = 'blog_entry.edit'
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
    return flask.render_template('blog_entry/edit.html')

@page.route('/blog_entry/<id>/update', methods=['POST'])
@require_login
@functools.partial(with_blog_entry, lang='all')
def update():
    subskey = 'blog_entry.edit'
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
    data['id'] = flask.g.stash.get('blog_entry_id')
    ok = flask.g.api.update_blog_entry(**data)
    if not ok:
        flask.g.stash['error'] = flask.g.api.last_error()

    del flask.session[subskey][subs]
    return flask.render_template('blog_entry/update.html')

import app
import flask
import functools
import time
import uuid

page = flask.Blueprint('track', __name__)
COLUMNS = [
    'name',
    'name#ja',
    'room_id',
    'sort_order'
]
REQUIRED = {
    'name': True,
    'room_id': True
}

with_track = app.hooks.with_track

@page.route('/track/<id>/view')
@functools.partial(with_track, lang='all')
def view():
    lang = flask.g.lang
    conf_id = flask.g.stash.get('track').get('conference_id')
    conf = app.api.lookup_conference(id=conf_id, lang=lang)
    if not conf:
      return flask.abort(404)
    flask.g.stash['conference'] = conf
    return flask.render_template('track/view.html')

@page.route('/track/<id>/edit', methods=['POST'])
@functools.partial(with_track, lang='all')
def edit():
    # For this action, merge the new values withe track
    # object, so that we can show the user the edits
    v = {}
    for k in COLUMNS:
        if k not in flask.request.values:
            continue
        if flask.request.values[k] is None:
            continue
        v[k] = flask.request.values[k]

    c = flask.g.stash.get('track')
    h = {}
    for k in COLUMNS:
        if k in v:
            h[k] = v[k]
        elif k in c and c[k] is not None:
            h[k] = c[k]
    flask.g.stash['new_track'] = h

    subs = str(uuid.uuid4())
    subskey = 'track.edit'
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
    return flask.render_template('track/edit.html')

@page.route('/track/<id>/update', methods=['POST'])
@functools.partial(with_track, lang='all')
def update():
    subskey = 'track.edit'
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
    data['id'] = flask.g.stash.get('track_id')
    data['user_id'] = flask.session['user_id']
    ok = app.api.update_track(**data)
    if not ok:
        flask.g.stash['error'] = app.api.last_error()

    del flask.session[subskey][subs]
    return flask.render_template('track/update.html')



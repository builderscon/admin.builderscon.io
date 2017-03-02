import app
import flask
import functools
import time
import uuid
import pytz
import iso8601
from datetime import datetime

page = flask.Blueprint('session', __name__)
COLUMNS = [
    'abstract',
    'abstract#ja',
    'confirmed',
    'has_interpretation',
    'material_level',
    'materials_release',
    'memo'
    'photo_release',
    'recording_release',
    'room_id',
    'selection_result_sent',
    'session_type_id',
    'slide_language',
    'slide_url',
    'sort_order',
    'spoken_language',
    'status',
    'title',
    'title#ja',
    'video_url',
]

REQUIRED = {
    'id': True,
}
REQUIRED_BY_LANG = {
    'title': True,
    'abstract': True
}

with_session = app.hooks.with_session
with_associated_conference = app.hooks.with_associated_conference

@page.route('/session/<id>/view')
@functools.partial(with_session, lang='all')
@functools.partial(with_associated_conference, id_getter=lambda: flask.g.stash.get('session').get('conference_id'))
def view():
    return flask.render_template('session/view.html')

@page.route('/session/create', methods=['POST'])
def create():
    subskey = 'session.create'
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
    new_session = app.api.create_session(**data)
    if not new_session:
        flask.g.stash['errors'] = [{'error': app.api.last_error()}]
        return flask.render_template('session/input.html')

    del flask.session[subskey][subs]
    flask.g.stash['session'] = new_session
    return flask.render_template('session/create.html')

@page.route('/session/<id>/edit', methods=['POST'])
@functools.partial(with_session, lang='all')
@functools.partial(with_associated_conference, id_getter=lambda: flask.g.stash.get('session').get('conference_id'))
def edit():
    # starts_on_date and starts_on_time must be concatenated into a single value
    values = flask.request.values.to_dict()
    if 'starts_on_time' in values:
        starts_on_time = values['starts_on_time']
        del values['starts_on_time']
    if 'starts_on_date' in values:
        starts_on_date = values['starts_on_date']
        del values['starts_on_date']

    if starts_on_time and starts_on_date:
        conference = flask.g.stash.get('conference')
        tz = pytz.timezone(conference.get('timezone', 'utc'))
        offset = tz.utcoffset(datetime.utcnow()).total_seconds()
        s = '%sT%s%s%02d%02d' %(starts_on_date, starts_on_time, '-' if offset < 0 else '+', offset/3600, offset%3600)
        starts_on = iso8601.parse_date(s).astimezone(tz)
        if starts_on:
            values['starts_on'] = starts_on

    # For this action, merge the new values withe session
    # object, so that we can show the user the edits
    v = {}
    for k in COLUMNS:
        if k not in values:
            continue
        if values[k] is None:
            continue
        v[k] = values[k]

    c = flask.g.stash.get('session')
    h = {}
    for k in COLUMNS:
        if k in v:
            h[k] = v[k]
        elif k in c and c[k]:
            h[k] = c[k]
    flask.g.stash['new_session'] = h

    subs = str(uuid.uuid4())
    subskey = 'session.edit'
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
    return flask.render_template('session/edit.html')

@page.route('/session/<id>/update', methods=['POST'])
@functools.partial(with_session, lang='all')
def update():
    subskey = 'session.edit'
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
    data['id'] = flask.g.stash.get('session_id')
    data['user_id'] = flask.session['user_id']

    for boolkey in ['has_interpretation', 'confirmed']:
        if boolkey in data:
            data[boolkey] = not not data[boolkey]

    if 'sort_order' in data:
        if not data['sort_order']:
            del data['sort_order']
        else:
            data['sort_order'] = int(data['sort_order'])
    print(data)
    ok = app.api.update_session(**data)
    if not ok:
        flask.g.stash['error'] = app.api.last_error()

    del flask.session[subskey][subs]
    return flask.render_template('session/update.html')
import app
import flask
import functools
import pytz
import time
import uuid

page = flask.Blueprint('conference', __name__)
COLUMNS = [
    'cfp_lead_text',
    'cfp_lead_text#ja',
    'cfp_pre_submit_instructions',
    'cfp_pre_submit_instructions#ja',
    'cfp_post_submit_instructions',
    'cfp_post_submit_instructions#ja',
    'contact_information',
    'contact_information#ja',
    'cover_url',
    'description',
    'description#ja',
    'series_id',
    'slug',
    'status',
    'sub_title',
    'sub_title#ja',
    'timezone_available',
    'timezone'
    'title',
    'title#ja',
]

with_conference = app.hooks.with_conference
with_conference_series_list = app.hooks.with_conference_series_list
with_venue_list = app.hooks.with_venue_list

@page.route('/conference')
def index():
    return flask.render_template('conference/index.html')

@page.route('/conference/<id>/view')
@functools.partial(with_conference, lang='all')
@with_conference_series_list
@with_venue_list
def view():
    flask.g.stash['timezones'] = pytz.all_timezones
    return flask.render_template('conference/view.html')

@page.route('/conference/<id>/edit', methods=['POST'])
@functools.partial(with_conference, lang='all')
def edit():
    # For this action, merge the new values withe conference
    # object, so that we can show the user the edits
    v = {}
    for k in COLUMNS:
        if k not in flask.request.values:
            continue
        if flask.request.values[k] is None:
            continue
        v[k] = flask.request.values[k]

    c = flask.g.stash.get('conference')
    h = {}
    for k in COLUMNS:
        if k in v:
            h[k] = v[k]
        elif k in c and c[k] is not None:
            h[k] = c[k]
    flask.g.stash['new_conference'] = h

    subs = str(uuid.uuid4())
    subskey = 'conference.edit'
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
    return flask.render_template('conference/edit.html')

@page.route('/conference/<id>/update', methods=['POST'])
@functools.partial(with_conference, lang='all')
def update():
    subskey = 'conference.edit'
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
    data['id'] = flask.g.stash.get('conference_id')
    data['user_id'] = flask.session['user_id']
    ok = app.api.update_conference(**data)
    if not ok:
        flask.g.stash['error'] = app.api.last_error()

    del flask.session[subskey][subs]
    return flask.render_template('conference/update.html')

@page.route('/conference/<id>/sessions')
@with_conference
def sessions():
    sessions = app.api.list_sessions(
        conference_id=flask.g.stash.get('conference_id'),
        lang=flask.g.lang,
        status=['accepted', 'rejected']
    )
    flask.g.stash['sessions'] = sessions;
    return flask.render_template('conference/sessions.html')

@page.route('/conference/<id>/blog_entries')
@with_conference
def blog_entries():
    blog_entries = app.api.list_blog_entries(
        conference_id=flask.g.stash.get('conference_id'),
        lang=flask.g.lang,
        status=['public', 'private']
    )
    flask.g.stash['blog_entries'] = blog_entries or [];
    return flask.render_template('conference/blog_entries.html')


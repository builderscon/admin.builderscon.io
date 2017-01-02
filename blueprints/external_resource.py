import app
import flask
import functools
import urlparse
import copy

page = flask.Blueprint('external_resource', __name__)

require_login = app.hooks.require_login
with_external_resource = app.hooks.with_external_resource

COLUMNS = [
    'id',
    'conference_id',
    'title',
    'title#ja',
    'description',
    'description#ja',
    'url',
    'sort_order',
]

def to_int(s):
    try:
        return int(s)
    except ValueError:
        return 0


def is_safe_url(target):
    ref_url = urlparse.urlparse(flask.request.host_url)
    test_url = urlparse.urlparse(urlparse.urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in flask.request.values.get('next_url'), flask.request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target
    return flask.url_for('/')


@page.route('/external_resource/create', methods=['GET'])
def create_external_resource_get():
    conference_id = flask.request.args.get('conference_id')
    if not conference_id:
        flask.g.stash['error'] = "conference_id must be specified in URL query string"
        flask.g.stash['external_resource'] = {}
        return flask.render_template('/external_resource/create.html')
    else:
        flask.g.stash['conference_id'] = conference_id
        flask.g.stash['external_resource'] = {}
        return flask.render_template('/external_resource/create.html')


@page.route('/external_resource/create', methods=['POST'])
@require_login
def create_external_resource_post():
    new_external_resource = {}
    for key in COLUMNS:
        if key in flask.request.values:
            new_external_resource[key] = flask.request.values.get(key)
    new_external_resource['sort_order'] = to_int(flask.request.values.get('sort_order'))

    args = copy.deepcopy(new_external_resource)
    args['user_id'] = flask.g.stash.get('user').get('id')
    ok = app.api.create_external_resource(**args)

    if ok:
        redirect_url = get_redirect_target()
        return flask.redirect(redirect_url, code=303)
    else:
        # retain new input in the rendered page
        flask.g.stash['error'] = app.api.last_error()
        flask.g.stash['conference_id'] = flask.request.values.get('conference_id')
        flask.g.stash['external_resource'] = new_external_resource
        return flask.render_template('external_resource/create.html')


@page.route('/external_resource/<id>/update', methods=['GET'])
@functools.partial(with_external_resource, lang='all')
def update_external_resource_get():
    return flask.render_template('external_resource/update.html')


@page.route('/external_resource/<id>/update', methods=['POST'])
@functools.partial(with_external_resource, lang='all')
@require_login
def update_external_resource_post():
    # old is given by with_external_resource() hook
    old_external_resource = flask.g.stash.get('external_resource')

    new_external_resource = {}
    # merge old with request (i.e. HTML form)
    for key in COLUMNS:
        if key in flask.request.values:
            new_external_resource[key] = flask.request.values.get(key)
        elif key in old_external_resource:
            new_external_resource[key] = old_external_resource.get(key)
    new_external_resource['sort_order'] = to_int(new_external_resource.get('sort_order'))

    args = copy.deepcopy(new_external_resource)
    args['user_id'] = flask.g.stash.get('user').get('id')
    ok = app.api.update_external_resource(**args)

    if ok:
        redirect_url = get_redirect_target()
        return flask.redirect(redirect_url, code=303)
    else:
        # retain new input in the rendered page
        flask.g.stash['external_resource'] = new_external_resource
        flask.g.stash['error'] = app.api.last_error()
        return flask.render_template('external_resource/update.html')


@page.route('/external_resource/<id>/delete', methods=['GET'])
@functools.partial(with_external_resource, lang='all')
def delete_external_resource_get():
    return flask.render_template('external_resource/delete.html')


@page.route('/external_resource/<id>/delete', methods=['POST'])
@functools.partial(with_external_resource, lang='all')
@require_login
def delete_external_resource_post():
    ok = app.api.delete_external_resource(
        id=flask.request.values.get('id'),
        user_id=flask.g.stash.get('user').get('id')
    )
    if ok:
        redirect_url = get_redirect_target()
        return flask.redirect(redirect_url, code=303)
    else:
        # retain new input in the rendered page
        flask.g.stash['error'] = app.api.last_error()
        return flask.render_template('external_resource/delete.html')
import admin
import flask
import flasktools
import functools
import octav

@admin.app.before_request
def detect_default_language():
    flask.g.lang = admin.get_locale()

def load_logged_in_user():
    print("load_logged_in_user")
    has_octav_session = True
    for k in ['octav_session_id', 'octav_session_expires']:
        if k not in flask.session:
            print("Could not find key %s" % k)
            has_octav_session = False
            break

    if not has_octav_session:
        for k in ['access_token', 'user_id']:
            if k not in flask.session:
                return False

        s = flask.g.api.new_session(flask.session['access_token'], flask.session['auth_via'])
        if s is None:
            return False
        flask.session['octav_session_id'] = s.sid
        flask.session['octav_session_expires'] = s.expires
    else:
        sid = flask.session['octav_session_id']
        print("session exists %s" % sid)
        expires = flask.session['octav_session_expires']
        f = functools.partial(flask.g.api.create_client_session, flask.session['access_token'], flask.session['auth_via'])
        s = octav.Session(flask.g.api, f, sid, expires)
        v = s.renew()
        print("result of renew %s" % v)
        if v is None:
            return False
        if v:
            # Update the stored octav session ID
            flask.session['octav_session_id'] = s.sid
            flask.session['octav_session_expires'] = s.expires
    flask.g.api = s
    if 'user_id' in flask.session:
        user = flask.g.api.lookup_user(flask.session.get('user_id'))
        if user:
            flask.g.stash['user'] = user
            return True
        del flask.session['user_id']
    return False

def load_user_only(cb, **args):
    load_logged_in_user()
    return cb(**args)

def load_user_or_login(cb, **args):
    if load_logged_in_user():
        return cb(**args)
    next_url = flask.request.path + "?" + flasktools.urlencode(flask.request.args)
    query = flasktools.urlencode({'.next': next_url})
    return flask.redirect("/login?" + query)

def check_login(cb, **args):
    return functools.update_wrapper(functools.partial(load_user_only, cb, **args), cb)

# Check if we have the user session field pre-populated.
def require_login(cb, **args):
    return functools.update_wrapper(functools.partial(load_user_or_login, cb, **args), cb)

def require_email(cb, **args):
    return functools.update_wrapper(functools.partial(check_email, cb, **args), cb)

def check_email(cb, **args):
    user = flask.g.stash.get('user')
    if not user:
        return "require_login must be called first", 500

    if not user.get('email'):
        next_url = flask.request.path + "?" + flasktools.urlencode(flask.request.args)
        flask.session['next_url_after_email_registration'] = next_url
        return flask.redirect('/user/email/register')

    return cb(**args)

def with_associated_conference(cb, id_getter, lang=None):
    def _load_associated_conference(cb, id_getter):
        conf_id = id_getter()
        conf = flask.g.api.lookup_conference(id=conf_id, lang=lang or flask.g.lang)
        if not conf:
          return flask.abort(404)
        flask.g.stash['conference'] = conf
        return cb()
    return functools.update_wrapper(functools.partial(_load_associated_conference, cb, id_getter), cb)

def with_conference(cb, lang=None):
    def _load_conference(cb, id, lang):
        conf = flask.g.api.lookup_conference(id=id, lang=lang or flask.g.lang)
        if not conf:
            return flask.abort(404)
        flask.g.stash['conference'] = conf
        flask.g.stash['conference_id'] = id
        return cb()

    return functools.update_wrapper(functools.partial(_load_conference, cb, lang=lang), cb)

def with_conference_list(cb, **args):
    def _load_conference_list(cb, **args):
        if 'lang' not in args:
            args['lang'] = flask.g.lang

        conferences = flask.g.api.list_conference(**args)
        if not conferences:
            return flask.abort(404)
        flask.g.stash['conferences'] = conferences
        return cb()

    return functools.update_wrapper(functools.partial(_load_conference_list, cb, **args), cb)

def with_conference_series_list(cb):
    def _load_conference_series_list(cb):
        serieses = flask.g.api.list_conference_series()
        if not serieses:
            return flask.abort(404)
        flask.g.stash['conference_series'] = serieses
        return cb()

    return functools.update_wrapper(functools.partial(_load_conference_series_list, cb), cb)

def with_track(cb, lang=None):
    def _load_track(cb, id, lang):
        if lang is None:
            lang = flask.g.lang
        track = flask.g.api.lookup_track(id=id, lang=lang)
        if not track:
            return flask.abort(404)
        flask.g.stash['track_id'] = id
        flask.g.stash['track'] = track
        return cb()

    return functools.update_wrapper(functools.partial(_load_track, cb, lang=lang), cb)

def with_venue(cb, lang=None):
    def _load_venue(cb, id, lang):
        if lang is None:
            lang = flask.g.lang
        venue = flask.g.api.lookup_venue(id=id, lang=lang)
        if not venue:
            return flask.abort(404)
        flask.g.stash['venue'] = venue
        return cb()

    return functools.update_wrapper(functools.partial(_load_venue, cb, lang=lang), cb)

def with_venue_list(cb, lang=None):
    def _load_venue_list(cb, lang):
        venues = flask.g.api.list_venue(lang=lang or flask.g.lang)
        flask.g.stash['venues'] = venues or []
        return cb()

    return functools.update_wrapper(functools.partial(_load_venue_list, cb, lang=lang), cb)

def with_session_type(cb, lang=None):
    def _load_session_type(cb, id, lang):
        session_type = flask.g.api.lookup_session_type(id=id, lang=lang or flask.g.lang)
        if not session_type:
            return flask.abort(404)
        flask.g.stash['session_type_id'] = id
        flask.g.stash['session_type'] = session_type
        return cb()
    return functools.update_wrapper(functools.partial(_load_session_type, cb, lang=lang), cb)

def with_sponsor(cb, lang=None):
    def _load_sponsor(cb, id, lang):
        sponsor = flask.g.api.lookup_sponsor(id=id, lang=lang or flask.g.lang)
        if not sponsor:
            return flask.abort(404)
        flask.g.stash['sponsor_id'] = id
        flask.g.stash['sponsor'] = sponsor
        return cb()
    return functools.update_wrapper(functools.partial(_load_sponsor, cb, lang=lang), cb)

def with_featured_speaker(cb, lang=None):
    def _load_featured_speaker(cb, id, lang):
        featured_speaker = flask.g.api.lookup_featured_speaker(id=id, lang=lang or flask.g.lang)
        if not featured_speaker:
            return flask.abort(404)
        flask.g.stash['featured_speaker_id'] = id
        flask.g.stash['featured_speaker'] = featured_speaker
        return cb()
    return functools.update_wrapper(functools.partial(_load_featured_speaker, cb, lang=lang), cb)

def with_blog_entry(cb, lang=None):
    def _load_blog_entry(cb, id, lang):
        blog_entry = flask.g.api.lookup_blog_entry(id=id, lang=lang or flask.g.lang)
        if not blog_entry:
            return flask.abort(404)
        flask.g.stash['blog_entry_id'] = id
        flask.g.stash['blog_entry'] = blog_entry
        return cb()
    return functools.update_wrapper(functools.partial(_load_blog_entry, cb, lang=lang), cb)

def with_session(cb, lang=None):
    def _load_session(cb, id, lang):
        session = flask.g.api.lookup_session(id=id, lang=lang or flask.g.lang)
        if not session:
            return flask.abort(404)
        flask.g.stash['session_id'] = id
        flask.g.stash['session'] = session
        return cb()
    return functools.update_wrapper(functools.partial(_load_session, cb, lang=lang), cb)

def with_external_resource(cb, lang=None):
    def _load_external_resource(cb, id, lang):
        external_resource = flask.g.api.lookup_external_resource(id=id, lang=lang or flask.g.lang)
        if not external_resource:
            return flask.abort(404)
        flask.g.stash['external_resource_id'] = id
        flask.g.stash['external_resource'] = external_resource
        return cb()
    return functools.update_wrapper(functools.partial(_load_external_resource, cb, lang=lang), cb)

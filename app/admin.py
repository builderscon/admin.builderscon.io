import config
import flask
import flask_babel
import os
import octav
import re
import sessionmgr

app = flask.Flask("admin")
babel = flask_babel.Babel(app)

def initialize():
    import blueprints
    app.register_blueprint(blueprints.api.page)
    app.register_blueprint(blueprints.auth.page)
    app.register_blueprint(blueprints.blog_entry.page)
    app.register_blueprint(blueprints.conference.page)
    app.register_blueprint(blueprints.root.page)
    app.register_blueprint(blueprints.session_type.page)
    app.register_blueprint(blueprints.track.page)
    app.register_blueprint(blueprints.venue.page)

    global cfg, api

    config_file = os.getenv("CONFIG_FILE")
    if not config_file:
        config_file = "config.json"
    cfg = config.Config(config_file)

    api = octav.Octav(**cfg.section('OCTAV'))
    app.secret_key = cfg.section('FLASK').get('secret')
    app.base_url = cfg.section('FLASK').get('base_url', 'https://admin.builderscon.io')
    app.session_interface = sessionmgr.build(os.getenv('SESSION_BACKEND', 'Redis'), cfg)

# Get the current locale
jarx = re.compile('^ja(?:-\w+)$')
@babel.localeselector
def get_locale():
    l = flask.request.args.get('lang')
    if not l:
        stash = flask.g.get('stash')
        if stash:
            u = stash.get('user')
            if u:
                l = u.get('lang', l)
        # This is silly, accept_languages.best_match doesn't
        # match against ja-JP if the arguments are just 'ja'
        # TODO: Lookup Accept-Language, and change its value
        # to make the matching easier
        if not l:
            l = flask.request.accept_languages.best_match(['ja', 'ja-JP', 'en'])
    if l:
        if jarx.match(l):
            l = 'ja'
        return l
    return 'en'

@app.before_request
def before_request_hook():
    lang = get_locale()
    flask.g.stash = dict(lang=lang)

@app.context_processor
def inject_template_vars():
    stash = flask.g.stash
    stash["flask_session"] = flask.session
    stash["url"] = flask.url_for
    return stash

@app.errorhandler(404)
def page_not_found(e):
    flask.g.stash["error"] = e
    return flask.render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    flask.g.stash["error"] = e
    print(e)
    return flask.render_template('errors/500.html'), 500



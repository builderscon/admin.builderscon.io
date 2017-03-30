
import admin
import hooks
admin.initialize()

import filters
import logging
import oauth
import requestlogger
import sys

assert hooks
assert filters

app = requestlogger.WSGILogger(
    admin.app,
    [logging.StreamHandler(sys.stdout)],
    requestlogger.ApacheFormatter()
)

def github_oauth():
    return oauth.start(oauth.github, admin.app.base_url + '/login/github/callback')

def facebook_oauth():
    return oauth.start(oauth.facebook, admin.app.base_url + '/login/facebook/callback')

def twitter_oauth():
    return oauth.start(oauth.twitter, admin.app.base_url + '/login/twitter/callback')

github_oauth_callback = oauth.github_callback
facebook_oauth_callback = oauth.facebook_callback
twitter_oauth_callback = oauth.twitter_callback


import json
import os

class Config(object):
    def populate_from_env(self, envname, section, key):
        v = os.getenv(envname)
        if v:
            c = self.section(section, create=True)
            c[key] = v

    def __init__(self, file):
        with open(file, 'r') as f:
            self.cfg = json.load(f)

        self.populate_from_env('OCTAV_CLIENT_DEBUG', 'OCTAV', 'debug')
        self.populate_from_env('OCTAV_CLIENT_KEY', 'OCTAV', 'key')
        self.populate_from_env('OCTAV_CLIENT_SECRET', 'OCTAV', 'secret')
        for t in ['GITHUB', 'FACEBOOK', 'TWITTER']:
            self.populate_from_env('ADMINWEB_%s_CLIENT_ID' % t, t, 'client_id')
            self.populate_from_env('ADMINWEB_%s_SECRET' % t, t, 'client_secret')
 
        for t in ['host', 'port', 'db']:
            self.populate_from_env('ADMINWEB_REDIS_%s' % t.upper(), t, t)

    def section(self, name, create=False):
        o = self.cfg.get(name)
        if o is None:
            if create:
                o = {}
                self.cfg[name] = o
            else:
                raise Exception("config section %s is missing" % (name))
        return o

    def googlemap_api_key(self):
        return self.cfg.get("GOOGLE_MAP").get("api_key")



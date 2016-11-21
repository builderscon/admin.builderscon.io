import json

class Config(object):
    def __init__(self, file):
        with open(file, 'r') as f:
            self.cfg = json.load(f)

    def section(self, name):
        o = self.cfg.get(name)
        if o is None:
            raise Exception("config section %s is missing" % (name))
        return o

    def googlemap_api_key(self):
        return self.cfg.get("GOOGLE_MAP").get("api_key")



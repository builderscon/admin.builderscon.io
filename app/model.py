import admin

def get_conference(id, lang='en'):
    key = 'conference.id.%s.%s' % (id, lang)
    conf = admin.cache.get(key)
    if conf:
        return conf

    conf = admin.api.lookup_conference(id=id, lang=lang)
    if conf:
        admin.cache.set(key, conf, 3600)
        return conf

    return None
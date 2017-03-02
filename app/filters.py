# coding:utf-8

import admin
import iso8601
import pytz

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
class Date(object):
    def __init__(self, jsonval, lang='en', timezone='UTC'):
        localtz = pytz.timezone(timezone)
        self.open = iso8601.parse_date(jsonval.get('open')).astimezone(localtz)
        self.close = iso8601.parse_date(jsonval.get('close')).astimezone(localtz)
        self.lang = lang

    def date(self):
        return '%d年%d月%d日'.decode('utf-8') % (self.open.year, self.open.month, self.open.day)

    def open_time(self):
        return '%02d:%02d' % (self.open.hour, self.open.minute)

    def close_time(self):
        return '%02d:%02d' % (self.close.hour, self.close.minute)

    def __str__(self):
        return self.date()



@admin.app.template_filter('date')
def date_filter(s, lang='en', timezone='UTC'):
    return Date(s, lang=lang, timezone=timezone)

@admin.app.template_filter('first_available_lang')
def first_available_lang(obj, field, langs=['ja']):
    for l in langs:
        key = field + '#' + l
        if key in obj:
            return obj.get(key)
    return obj.get(field)

@admin.app.template_filter('datepicker_value')
def datepicker_value(s, timezone='UTC'):
    localtz = pytz.timezone(timezone)
    return iso8601.parse_date(s).astimezone(localtz).date().isoformat()

@admin.app.template_filter('clockpicker_value')
def clockpicker_value(s, timezone='UTC'):
    localtz = pytz.timezone(timezone)
    return iso8601.parse_date(s).astimezone(localtz).time().isoformat()

@admin.app.template_filter('sort_dict_keys')
def sort_dict_keys(h):
    return sorted(h)

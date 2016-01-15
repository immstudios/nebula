from .common import *
from .constants import *

class MetaType(object):
    def __init__(self, title):
        self.title      = title
        self.namespace  = "site"
        self.editable   = False
        self.searchable = False
        self.class_     = TEXT
        self.default    = False
        self.settings   = False
        self.aliases    = {}

    def alias(self, lang='en-US'):
        if not lang in self.aliases:
            return self.title.replace("_"," ").capitalize()
        return self.aliases[lang][0]

    def col_header(self, lang='en-US'):
        if not lang in self.aliases:
            return self.title.replace("_"," ").capitalize()
        a, h = self.aliases[lang]
        if h is None:
            return a
        return h

    def pack(self):
        return {
                "title"      : self.title,
                "namespace"  : self.namespace,
                "editable"   : self.editable,
                "searchable" : self.searchable,
                "class"      : self.class_,
                "default"    : self.default,
                "settings"   : self.settings,
                "aliases"    : self.aliases
                }


class MetaTypes(dict):
    def __init__(self):
        super(MetaTypes, self).__init__()
        self.nstagdict = {}

    def __getitem__(self, key):
        return self.get(key, self._default())

    def _default(self):
        meta_type = MetaType("Unknown")
        meta_type.namespace  = "site"
        meta_type.editable   = 0
        meta_type.searchable = 0
        meta_type.class_     = TEXT
        meta_type.default    = ""
        meta_type.settings   = False
        return meta_type

    def ns_tags(self, ns):
        if not ns in self.nstagdict:
            result = []
            for tag in self:
                if self[tag].namespace in ["o", ns]:
                    result.append(self[tag].title)
            self.nstagdict[ns] = result
        return self.nstagdict[ns]

    def format_default(self, key):
        if not key in self:
            return False
        else:
            return self.format(key, self[key].default)

    def tag_alias(self, key, lang):
        if key in self:
            return self[key].alias(lang)
        return key

    def col_alias(self, key, lang):
        if key in self:
            return self[key].col_header(lang)
        return key


    def format(self, key, value):
        if key.startswith("can/"):  # user rights - always json
            return json.loads(value)

        if not key in self:
            return value
        mtype = self[key]

        if  key == "path":                return value.replace("\\","/")

        elif mtype.class_ == TEXT:        return value.strip()
        elif mtype.class_ == BLOB:        return value.strip()
        elif mtype.class_ == INTEGER:     return int(value)
        elif mtype.class_ == NUMERIC:     return float(value)
        elif mtype.class_ == BOOLEAN:     return int(value)
        elif mtype.class_ == DATETIME:    return float(value)
        elif mtype.class_ == TIMECODE:    return float(value)
        elif mtype.class_ == REGIONS:     return value if type(value) == dict else json.loads(value)
        elif mtype.class_ == FRACTION:    return str(value).strip().replace(":","/")

        elif mtype.class_ == SELECT:      return value
        elif mtype.class_ == CS_SELECT:   return value
        elif mtype.class_ == ENUM:        return int(value)
        elif mtype.class_ == CS_ENUM:     return int(value)
        elif mtype.class_ == SELECT:      return value
        elif mtype.class_ == CS_SELECT:   return value

        return value

    def unformat(self, key, value):
        mtype = self[key]
        if type(value) in (list, dict):
            return json.dumps(value)
        elif mtype.class_ == REGIONS or key.startswith("can/"):
            return json.dumps(value)
        return value


meta_types = MetaTypes()


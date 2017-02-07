import email
from nx import *


try:
    from urllib.request import urlopen
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
    from urllib2 import urlopen


def rfc822(timestamp):
    return  email.Utils.mktime_tz(email.Utils.parsedate_tz(timestamp))

class NewsItem(dict):
    pass

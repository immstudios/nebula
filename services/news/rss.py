import os
import urllib2

from .common import *

__all__ = ["rss_parser", "google_news_parser", "RSS"]

def rss_parser(self, item_data):
    item = NewsItem()
    try:
        guid = item_data.find("guid").text.strip()
        title = item_data.find("title").text.strip()
    except:
        return False

    description =  item_data.find("description").text
    description = description.strip() if description else ""

    pub_date = item_data.find("pubDate").text
    pub_date = rfc822(pub_date.strip()) if pub_date else time.time()

    item["identifier/guid"] = guid
    item["title"] = title
    item["article"] = description
    item["description"] = ""
    item["source"] = "" #TODO: Domain/RSS name here
    return item


def google_news_parser(item_data):
    item = NewsItem()
    try:
        guid = item_data.find("guid").text.strip()
        title = item_data.find("title").text.strip()
    except:
        return False

    title_elms = title.strip().split("-")
    title =  " ".join(title_elms[:-1]).strip()
    source = title_elms[-1].strip()

    if title.endswith("..."):
       logging.warning("{} ends with tripple dot. skipping".format(title))
       return False

    pub_date = item_data.find("pubDate").text
    pub_date = rfc822(pub_date.strip()) if pub_date else time.time()

    #TODO: parse article
#    desc1 = item_data.find("description").text.strip()
#    matcher = r".*font\ size=\"\-1\"\&gt\;(?P<article>.*?)\&lt\;.*"
#    m = re.match(matcher,desc1)
#    desc2 = m.group("article")

 #   if desc2.endswith("<b>...</b>"):
 #       desc2 = ". ".join(desc2.split(". ")[:-1]).strip()+"."

    item["title"]   = title
    item["identifier/guid"] = guid
    item["source"]  = source
    #item["article"] = re.sub(r"(\| foto (.*))\.",".",strip_tags(desc2)).replace("|"," ")

    return item




class RSS():
    parser = rss_parser

    def __init__(self, feed_url, parser=False):
        self.feed_url = feed_url
        self.parser = parser
        data = urlopen(self.feed_url).read()
        self.feed = xml(data).find("channel")

    @property
    def items(self):
        for item_data in self.feed.findall("item"):
            item = self.parser(item_data)
            if item:
                yield item

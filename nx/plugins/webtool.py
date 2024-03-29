__all__ = ["WebToolPlugin"]

import os

from nxtools import format_time, s2tc, slugify
from nx.plugins.common import get_plugin_path


class WebToolPlugin(object):
    gui = True
    native = True
    public = False

    def __init__(self, view, name):
        self.view = view
        self.name = name
        self["name"] = self.title

    def render(self, template):
        import jinja2

        tpl_dir = os.path.join(get_plugin_path("webtools"), self.name)
        jinja = jinja2.Environment(loader=jinja2.FileSystemLoader(tpl_dir))
        jinja.filters["format_time"] = format_time
        jinja.filters["s2tc"] = s2tc
        jinja.filters["slugify"] = slugify
        template = jinja.get_template("{}.html".format(template))
        return template.render(**self.context)

    def set_template(self, name):
        tpl_dir = os.path.join(get_plugin_path("webtools"), self.name)
        self.view.template_path = os.path.join(tpl_dir, "{}.html".format(name))

    def __getitem__(self, key):
        return self.view[key]

    def __setitem__(self, key, value):
        self.view[key] = value

    @property
    def context(self):
        return self.view.context

    def build(self, *args, **kwargs):
        pass

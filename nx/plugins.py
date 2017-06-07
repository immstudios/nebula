from nx import *

__all__ = ["plugin_path", "PlayoutPlugin"]


try:
    plugin_path = os.path.join(storages[int(config["plugin_storage"])].local_path, config["plugin_root"])
except (KeyError, IndexError):
    plugin_path = False
else:
    if not os.path.exists(plugin_path) and ismount(storages[int(config["plugin_storage"])].local_path):
        try:
            os.makedirs(plugin_path)
        except Exception:
            log_traceback()
            plugin_path = False


class PlayoutPluginSlot(object):
    def __init__(self, slot_type, **kwargs):
        self.slot_type = slot_type
        self.ops = kwargs

    def __getitem__(self, key):
        return self.ops.get(key, False)

    def __setitem__(self, key, value):
        self.ops[key] = value


class PlayoutPlugin(object):
    def __init__(self, channel):
        self.channel = channel
        self.id_layer = self.channel.feed_layer + 1
        self.slots = []
        self.tasks = []
        self.on_init()
        self.busy = False

    def add_slot(self, slot_type, **kwargs):
        self.slots.append(PlayoutPluginSlot(slot_type, **kwargs))

    def slot_value(self, index):
        return self.slots[index]["value"]

    def main(self):
        self.busy = True
        self.on_main()
        self.busy = False

    def layer(self, id_layer=False):
        if not id_layer:
            id_layer = self.id_layer
        return "{}-{}".format(self.channel.channel, id_layer)

    def query(self, query):
        return self.channel.server.query(query)

    def on_init(self):
        pass

    def on_change(self):
        pass

    def on_main(self):
        if not self.tasks:
            return
        if self.tasks[0]():
            del self.tasks[0]
            return



class WorkerPlugin(object):
    def __init__(self, service):
        self.service = service

    @property
    def config(self):
        return self.service.config

    def on_init(self):
        pass

    def on_main(self):
        pass

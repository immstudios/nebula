class Probe(object):
    title = "Generic Probe"
    def __init__(self):
        pass

    def __repr__(self):
        return self.title

    def accepts(self, asset):
        return False

    def work(self, asset):
        return asset


def guess_aspect (w, h):
    if 0 in [w, h]:
        return 0
    valid_aspects = [(16, 9), (4, 3), (2.35, 1)]
    ratio = float(w) / float(h)
    return "%s/%s" % min(valid_aspects, key=lambda x:abs((float(x[0])/x[1])-ratio))

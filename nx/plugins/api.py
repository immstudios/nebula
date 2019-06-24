
class APIPlugin(object):
    def auth(self, user):
        return bool(user.id)

    def main(self, **kwargs):
        pass


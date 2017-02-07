from nx import *

REQUIRED_PROTOCOL = 140000

class Sessions():
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        db = DB()
        db.query("SELECT s.id_user, u.meta FROM nx_sessions AS s, nx_users AS u WHERE s.key=%s AND u.id_object = s.id_user", [key])
        res = db.fetchall()
        if not res:
            return False
        id_user, meta = res[0]
        if not meta:
            return User(id_user)
        return User(meta=meta)

    def __delitem__(self, key):
        if key in self.data:
            del(self.data[key])

    def login(self, auth_key, params):
        if params.get("protocol", 0) < REQUIRED_PROTOCOL:
            return [400, "Your Firefly version is outdated.\nPlease download latest update from support website."]

        if self[auth_key]:
            return [200, "Already logged in"]

        if params.get("login") and params.get("password"):
            db = DB()
            user = get_user(params["login"], params["password"], db=db)
            if user:
                db.query("INSERT INTO nx_sessions (key, id_user, host, ctime, mtime) VALUES (%s, %s , %s, %s, %s)", [ auth_key, user.id, params.get("host", "unknown"), time.time(), time.time()])
                db.commit()
                return [200, "Logged in"]
            else:
                return [403, "Incorrect login/password combination"]

        else:
            return [403, "Not logged in"]


    def logout(self, auth_key):
        user = self[auth_key]
        if not user:
            return [403, "Not logged in"]
        db = DB()
        db.query("DELETE FROM nx_sessions WHERE key = %s", [auth_key])
        db.commit()
        del self[auth_key]
        return [200, "ok"]

import time

from nx import *
from nx.objects import get_user, User

#TODO: sessions caching
class APIAuth():
    def __init__(self):
        pass

    def __getitem__(self, key):
        db = DB()
        db.query("SELECT id_user FROM nx_sessions WHERE key=%s", [key])
        try:
            user = User(db.fetchall()[0][0])
            return user
        except IndexError:
            return False


    def login(self, auth_key, **kwargs):
        if self[auth_key]:
            return 200, "Already logged in"
        login = kwargs.get("login")
        password = kwargs.get("password")
        if login and password:
            db = DB()
            user = get_user(login, password, db=db)
        else:
            return 403, "Not logged in"
        if not user:
            return 403, "Incorrect login/password combination"
        db.query(
            "INSERT INTO nx_sessions (key, id_user, host, ctime, mtime) VALUES (%s, %s , %s, %s, %s)",
            [auth_key, user.id, params.get("host", "unknown"), time.time(), time.time()]
            )
        db.commit()
        return 200, "Logged in"


    def logout(self, auth_key):
        user = self[auth_key]
        if not user:
            return 403, "Not logged in"
        db = DB()
        db.query("DELETE FROM nx_sessions WHERE key = %s", [auth_key])
        db.commit()
        return 200, "OK"

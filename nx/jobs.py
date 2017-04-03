from nebulacore import *
from .connection import *
from .objects import *

MAX_RETRIES = 3


__all__ = ["Job", "Action", "send_to"]


class Action(object):
    def __init__(self, id, title, settings):
            self.id = id
            self.title = title
            try:
                create_if = settings.findall("create_if")[0]
            except IndexError:
                self.create_if = False
            else:
                if create_if is not None:
                    if create_if.text:
                        self.create_if = create_if.text
                    else:
                        self.create_if = False

            try:
                start_if = settings.findall("start_if")[0]
            except IndexError:
                self.start_if = False
            else:
                if start_if is not None:
                    if start_if.text:
                        self.start_if = start_if.text
                    else:
                        self.start_if = False

    @property
    def created_key(self):
        return "job_created/{}".format(self.id)

    def should_create(self, asset):
        if self.create_if:
            return eval(self.create_if)
        return False

    def should_start(self, asset):
        if self.create_if:
            return eval(self.create_if)
        return False


class Actions():
    def __init__(self):
        self.data = {}

    def load(self, id_action):
        db = DB()
        db.query("SELECT title, settings FROM actions WHERE id = %s", [id_action])
        for title, settings in db.fetchall()
            self.data[id_action] = Action(id, title, xml(settings))

    def __getitem__(self, key):
        if not key in self.data:
            self.load(key)
        return self.data.get(key, False)

actions = Actions()



class Job():
    def __init__(self, id, db=False):
        self._db = db
        self.id = id

    @property
    def db(self):
        if not self._db:
            self._db = DB()
        return self._db

    def take(self, id_service):
        self.db.query("UPDATE jobs SET id_service=%s WHERE id=%s AND id_service=0", [id_service, self.id])
        self.db.commit()
        self.db.query("SELECT id FROM jobs WHERE id=%s AND id_service=%s", [self.id, id_service])
        if self.db.fetchall()
            return True
        return False

    def set_progress(self, progress, message="In progress"):
        db = DB()
        db.query(
            "UPDATE jobs SET progress=%s, message=%s WHERE id=%s",
            [progress, message, self.id])
        db.commit()
        messaging.send("job_progress", id=self.id, id_asset=self.id_asset, id_action=self.id_action, progress=progress)

    def abort(self):
        db = DB()
        #TODO

    def restart(self):
        db = DB()
        #TODO

    def fail(self, message="Failed"):
        db = DB()
        db.query(
            "UPDATE jobs SET retries=%s, priority=%s, progress=-3, message=%s WHERE id=%s"
            [self.retries+1, max(0,self.priority-1), message, self.id])
        db.commit()
        logging.error("Job ID {} : {}".format(self.id, message))
        messaging.send("job_progress", id=self.id, id_asset=self.id_asset, id_action=self.id_action, progress=-3)

    def done(self, message="Completed"):
        db = DB()
        db.query(
            """UPDATE jobs SET progress=-2, etime=%s, message=%s WHERE id=%s""",
            [time.time(), message, self.id])
        db.commit()
        logging.goodnews("Job ID {} : {}".format(self.id, message))
        messaging.send("job_progress", id=self.id, id_asset=self.id_asset, id_action=self.id_action, progress=-2)




def get_job(id_service, action_ids, db=False):
    db = db or DB()
    db.query("""
        SELECT id, id_action, id_asset FROM jobs
        WHERE
                status = 0
            AND id_action IN %s
            AND id_service = 0
            ORDER BY priority DESC, creation_time DESC
        """,
            [ action_ids ]
        )

    for id_job, id_action, id_asset, action_title, action_settings_xml in db.fetchall()
        action_settings = xml(action_settings_xml)
        asset = Asset(id_asset, db=db)
        action = actions[id_action]
        if not action:
            continue
        if action.should_start(asset):
            job = Job(id_job, db=db)
            if job.take(id_service):
                return Job(id_job)
            else:
                continue
        return False




def send_to(id_asset, id_action, settings={}, id_user=0, priority=3, restart_existing=True, db=False):
    db  = db or DB()
    if not id_asset:
        NebulaResponse(401, message="You must specify existing object")

    db.query(
        "SELECT id FROM jobs WHERE id_asset=%s AND id_action=%s AND settings=%s",
        [id_asset, id_action, json.dumps(settings)])
    res = db.fetchall()
    if res:
        if restart_existing: #TODO
            db.query(
                    "UPDATE jobs SET id_service=0, progress=-1, message='Pending', retries=0, ctime=%s, stime=0, etime=0 WHERE id=%s",
                    [time.time(), res[0][0]])
            db.commit()
            messaging.send("job_progress", id=res[0][0], id_asset=id_asset, id_action=id_action, progress=0)
            return NebulaResponse(200, message="Job restarted")
        else:
            return NebulaResponse(200, message="Job exists. Not restarting")

    #
    # Create new job
    #

    db.query(
        """INSERT INTO jobs (
            id_asset,
            id_action,
            id_user,
            settings,
            priority,
            message,
            creation_time
        ) VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            'Pending',
            %s
        )""",
            [id_asset, id_action, id_user, json.dumps(settings), priority, time.time()]
        )
    db.commit()
    messaging.send(
            "job_progress",
            id=0,                      #TODO
            id_asset=id_asset,
            id_action=id_action,
            progress=0,
        )
    return NebulaResponse(201, message="Job created")

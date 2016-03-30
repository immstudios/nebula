from nx import *

MAX_RETRIES = 3

class Job():
    def __init__(self, id_service,  actions=[], id_asset=False):
        self.id = False
        self.id_asset = id_asset
        self.id_service = id_service
        self.id_action = False
        self.settings = False
        self.retries = False
        if actions:
            self.get_job(actions)


    def get_job(self, actions):
        qactions = ", ".join([str(k) for k in actions])

        db = DB()
        db.query("""UPDATE jobs
            SET id_service = {id_service},
                stime      = {stime},
                etime      = 0
            WHERE
                id IN (SELECT id FROM jobs
                    WHERE progress   = -1
                    AND   id_service IN (0, {id_service})
                    AND   id_action  IN ({actions})
                    AND   retries    <  {max_retries}

                    ORDER BY priority DESC, ctime DESC LIMIT 1
                    )
                  """.format(
                      stime       = time.time(),
                      id_service  = self.id_service,
                      actions     = qactions,
                      max_retries = MAX_RETRIES
                      )
            )

        db.commit()

        db.query(
            "SELECT id, id_asset, id_action, settings, priority, retries FROM jobs WHERE progress=-1  AND id_service= %s",
            [self.id_service])

        for id, id_asset, id_action, settings, priority, retries in db.fetchall():
            logging.debug("New job found")
            self.id = id
            self.id_asset = id_asset
            self.id_action = id_action
            self.settings = settings
            self.priority = priority
            self.retries = retries
            break


    def __len__(self):
        return bool(self.id)

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





def send_to(id_asset, id_action, settings={}, id_user=0, priority=1, restart_existing=True, db=False):
    db  = db or DB()
    if not id_asset:
        return 401, "You must specify existing object"

    db.query(
        "SELECT id FROM jobs WHERE id_asset=%s AND id_action=%s AND settings=%s",
        [id_asset, id_action, json.dumps(settings)])
    res = db.fetchall()
    if res:
        if restart_existing:
            db.query(
                    "UPDATE jobs SET id_service=0, progress=-1, message='Pending', retries=0, ctime=%s, stime=0, etime=0 WHERE id=%s",
                    [time.time(), res[0][0]])
            db.commit()
            messaging.send("job_progress", id=res[0][0], id_asset=id_asset, id_action=id_action, progress=-1)
            return 200, "Job restarted"
        else:
            return 200, "Job exists. Not restarting"


    db.query(
        "INSERT INTO jobs (id_asset, id_action, settings, id_service, priority, progress, retries, ctime, stime, etime, message, id_user)
                   VALUES (%s,       %s,         %s,      0,          1,        -1,       0,       %s,    0,     0,     'Pending', %s)"
                          [id_asset, id_action, settings, time.time(), id_user])
    db.commit()
    messaging.send("job_progress", id=0, id_asset=id_asset, id_action=id_action, progress=-1) #TODO: more realistic id_job
    return 201, "Job created"

#
# WORK IN PROGRESS
#

from nx import *

__all__ = ["api_jobs"]

def api_jobs(**kwargs):
    db = kwargs.get("db", DB())

    if "restart" in kwargs:
        jobs = [int(i) for i in kwargs["restart"]]
        db.query("""
            UPDATE jobs SET
                status=5,
                retries=0,
                creation_time=%s,
                start_time=NULL,
                end_time=NULL,
                message='Restart requested'
            WHERE
                id IN %s
            RETURNING id
            """,
            [time.time(), tuple(jobs)]
            )
        result = [r[0] for r in db.fetchall()]
        db.commit()
        #TODO: smarter message
        return {"response" : 200, "data" : result, "message" : "Jobs restarted"}

    if "abort" in kwargs:
        jobs = [int(i) for i in kwargs["abort"]]
        db.query("""
            UPDATE jobs SET
                status=4,
                end_time=%s,
                message='Aborted'
            WHERE
                id IN %s
            RETURNING id
            """,
            [time.time(), tuple(jobs)]
            )
        result = [r[0] for r in db.fetchall()]
        db.commit()
        #TODO: smarter message
        return {"response" : 200, "data" : result, "message" : "Jobs abort"}


    return {"response" : 501, "message" : "Not implemented"}

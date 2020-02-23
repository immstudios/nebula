from .common import *

def format_status(key, asset):
    colored = "\033[{}m{:<8}\033[0m"
    return {
            OFFLINE  : colored.format(31, "OFFLINE"),
            ONLINE   : colored.format(32, "ONLINE"),
            CREATING : colored.format(33, "CREATING"),
            TRASHED  : colored.format(34, "TRASHED"),
            ARCHIVED : colored.format(34, "ARCHIVE"),
            RESET    : colored.format(33, "RESET"),
        }[asset[key]]

def format_title(key, asset):
    return "{:<30}".format(asset[key])

formats = {
        "id" : lambda key, asset: "{:<5}".format(asset[key]),
        "status" : format_status,
        "title" : lambda key, asset: "{:<24}".format(asset[key]),
    }




cols = ["id", "status", "title", "ctime", "mtime"]


def j(*args):
    print
    db = DB()
    db.query("""
        SELECT
            j.id,
            j.id_action,
            j.settings,
            j.priority,
            j.retries,
            j.status,
            j.progress,
            j.message,
            j.creation_time,
            j.start_time,
            j.end_time,
            a.meta
        FROM
            jobs AS j,
            assets AS a
        WHERE
            a.id = j.id_asset
        AND j.status in (0,1,5)

        ORDER BY
            id DESC LIMIT 50
            """)

    for id, id_action, settings, priority, retries, status, progress, message, creation_time, start_time, end_time, meta in db.fetchall():
        asset = Asset(meta=meta)

        l = "{:<30}".format(asset)
        l+= "{} {:.02f}%\n".format(status, progress)

        try:
            sys.stdout.write(l)
            sys.stdout.flush()
        except IOError:
            pass

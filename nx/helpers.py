import os
import time
import smtplib
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from nxtools import logging, log_traceback, datestr2ts

from nx.db import DB
from nx.core import config, storages, get_hash
from nx.messaging import messaging
from nx.objects import Asset, Item, Event, Bin, User
from nx.enum import MediaType, RunMode

try:
    import mistune  # noqa
    has_mistune = True
except ModuleNotFoundError:
    has_mistune = False


def get_user(login, password, db=False):
    if not db:
        db = DB()
    try:
        db.query(
            """
            SELECT meta FROM users
            WHERE login=%s AND password=%s
            """,
            [login, get_hash(password)]
        )
    except ValueError:
        return False
    res = db.fetchall()
    if not res:
        return False
    return User(meta=res[0][0])


def asset_by_path(id_storage, path, db=False):
    id_storage = str(id_storage)
    path = path.replace("\\", "/")
    if not db:
        db = DB()
    db.query("""
            SELECT id, meta FROM assets
                WHERE media_type = %s
                AND meta->>'id_storage' = %s
                AND meta->>'path' = %s
        """, [MediaType.FILE, id_storage, path])
    for id, meta in db.fetchall():
        return Asset(meta=meta, db=db)
    return False


def asset_by_full_path(path, db=False):
    if not db:
        db = DB()
    for id_storage in storages:
        if path.startswith(storages[id_storage].local_path):
            return asset_by_path(
                id_storage,
                path.lstrip(storages[id_storage]["path"]),
                db=db
            )
    return False


def meta_exists(key, value, db=False):
    if not db:
        db = DB()
    db.query(
        "SELECT id, meta FROM assets WHERE meta->>%s = %s",
        [str(key), str(value)]
    )
    for _, meta in db.fetchall():
        return Asset(meta=meta, db=db)
    return False


def get_day_events(id_channel, date, num_days=1):
    chconfig = config["playout_channels"][id_channel]
    start_time = datestr2ts(
        date,
        *chconfig.get("day_start", [6, 0])
    )
    end_time = start_time + (3600*24*num_days)
    db = DB()
    db.query(
        """
        SELECT id, meta
        FROM events
        WHERE id_channel=%s
        AND start > %s
        AND start < %s
        """,
        (id_channel, start_time, end_time)
    )
    for _, meta in db.fetchall():
        yield Event(meta=meta)


def get_bin_first_item(id_bin, db=False):
    if not db:
        db = DB()
    db.query(
        """
        SELECT id, meta FROM items
        WHERE id_bin=%s
        ORDER BY position LIMIT 1
        """,
        [id_bin]
    )
    for _, meta in db.fetchall():
        return Item(meta=meta, db=db)
    return False


def get_item_event(id_item, **kwargs):
    db = kwargs.get("db", DB())
    db.query(
        """
        SELECT e.id, e.meta
        FROM items AS i, events AS e
        WHERE e.id_magic = i.id_bin
        AND i.id = {}
        AND e.id_channel in ({})
        """.format(
            id_item,
            ", ".join([str(f) for f in config["playout_channels"].keys()])
        )
    )
    for _, meta in db.fetchall():
        return Event(meta=meta, db=db)
    return False


def get_item_runs(id_channel, from_ts, to_ts, db=False):
    db = db or DB()
    db.query(
        """
        SELECT id_item, start, stop
        FROM asrun
        WHERE start >= %s
        AND start < %s
        ORDER BY start DESC
        """,
        [int(from_ts), int(to_ts)]
    )
    result = {}
    for id_item, start, stop in db.fetchall():
        if id_item not in result:
            result[id_item] = (start, stop)
    return result


def get_next_item(item, **kwargs):
    db = kwargs.get("db", DB())
    force = kwargs.get("force", False)
    if type(item) == int and item > 0:
        current_item = Item(item, db=db)
    elif isinstance(item, Item):
        current_item = item
    else:
        logging.error(f"Unexpected get_next_item argument {item}")
        return False

    logging.debug(f"Looking for an item following {current_item}")
    current_bin = Bin(current_item["id_bin"], db=db)

    items = current_bin.items
    if force == "prev":
        items.reverse()

    for item in items:
        if (force == "prev" and item["position"] < current_item["position"]) \
                or (
                    force != "prev" and
                    item["position"] > current_item["position"]
                ):
            if item["item_role"] == "lead_out" and not force:
                logging.info("Cueing Lead In")
                for i, r in enumerate(current_bin.items):
                    if r["item_role"] == "lead_in":
                        return r
                else:
                    next_item = current_bin.items[0]
                    next_item.asset
                    return next_item
            if item["run_mode"] == RunMode.RUN_SKIP:
                continue
            item.asset
            return item
    else:
        current_event = get_item_event(item.id, db=db)
        direction = ">"
        order = "ASC"
        if force == "prev":
            direction = "<"
            order = "DESC"
        db.query(
            f"""
            SELECT meta FROM events
            WHERE id_channel = %s and start {direction} %s
            ORDER BY start {order} LIMIT 1
            """,
            [current_event["id_channel"], current_event["start"]]
        )
        try:
            next_event = Event(meta=db.fetchall()[0][0], db=db)
            if not next_event.bin.items:
                logging.debug("Next playlist is empty")
                raise Exception
            if next_event["run_mode"] and not kwargs.get(
                "force_next_event",
                False
            ):
                logging.debug("Next playlist run mode is not auto")
                raise Exception
            if force == "prev":
                next_item = next_event.bin.items[-1]
            else:
                next_item = next_event.bin.items[0]
            next_item.asset
            return next_item
        except Exception:
            logging.info("Looping current playlist")
            next_item = current_bin.items[0]
            next_item.asset
            return next_item


def bin_refresh(bins, **kwargs):
    bins = [b for b in bins if b]
    if not bins:
        return True
    db = kwargs.get("db", DB())
    sender = kwargs.get("sender", False)
    for id_bin in bins:
        b = Bin(id_bin, db=db)
        b.save(notify=False)
    bq = ", ".join([str(b) for b in bins if b])
    changed_events = []
    db.query(
        f"""
        SELECT e.meta FROM events as e, channels AS c
        WHERE
            c.channel_type = 0 AND
            c.id = e.id_channel AND
            e.id_magic IN ({bq})
        """
    )
    for meta, in db.fetchall():
        event = Event(meta=meta, db=db)
        if event.id not in changed_events:
            changed_events.append(event.id)
    logging.debug(
        f"Bins changed {bins}.",
        f"Initiator {kwargs.get('initiator', logging.user)}"
    )
    messaging.send(
            "objects_changed",
            sender=sender,
            objects=bins,
            object_type="bin",
            initiator=kwargs.get("initiator", None)
        )
    if changed_events:
        logging.debug(
            f"Events changed {bins}."
            f"Initiator {kwargs.get('initiator', logging.user)}"
        )
        messaging.send(
                "objects_changed",
                sender=sender,
                objects=changed_events,
                object_type="event",
                initiator=kwargs.get("initiator", None)
            )
    return True


def html2email(html):
    msg = MIMEMultipart("alternative")
    text = "no plaitext version available"
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    msg.attach(part1)
    msg.attach(part2)

    return msg


def markdown2email(text):
    if has_mistune:
        msg = MIMEMultipart("alternative")
        html = mistune.html(text)
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        msg.attach(part1)
        msg.attach(part2)
        return msg
    else:
        return MIMEText(text, "plain")


def send_mail(to, subject, body, **kwargs):
    if type(to) == str:
        to = [to]
    default_reply_address = config.get(
        "mail_from",
        f"Nebula <{config['site_name']}@nebulabroadcast.com>"
    )
    reply_address = kwargs.get("from", default_reply_address)
    smtp_host = config.get("smtp_host", "localhost")
    smtp_user = config.get("smtp_user", False)
    smtp_pass = config.get("smtp_pass", False)

    if isinstance(body, MIMEMultipart):
        msg = body
    else:
        msg = MIMEText(body)

    msg['Subject'] = subject
    msg['From'] = reply_address
    msg['To'] = ",".join(to)
    if config.get("smtp_ssl", False):
        smtp_port = config.get("smtp_port", 25)
        s = smtplib.SMTP_SSL(smtp_host, port=smtp_port)
    else:
        smtp_port = config.get("smtp_port", 465)
        s = smtplib.SMTP(smtp_host, port=smtp_port)
    if smtp_user and smtp_pass:
        s.login(smtp_user, smtp_pass)
    s.sendmail(reply_address, [to], msg.as_string())


def cg_download(target_path, method, timeout=10, verbose=True, **kwargs):
    start_time = time.monotonic()
    target_dir = os.path.dirname(os.path.abspath(target_path))
    cg_server = config.get("cg_server", "https://cg.immstudios.org")
    cg_site = config.get("cg_site", config["site_name"])
    if not os.path.isdir(target_dir):
        try:
            os.makedirs(target_dir)
        except Exception:
            logging.error(f"Unable to create output directory {target_dir}")
            return False
    url = f"{cg_server}/render/{cg_site}/{method}"
    try:
        response = requests.get(url, params=kwargs, timeout=timeout)
    except Exception:
        log_traceback("Unable to download CG item")
        return False
    if response.status_code != 200:
        logging.error(f"CG Download failed with code {response.status_code}")
        return False
    try:
        temp_path = target_path + ".creating"
        with open(temp_path, "wb") as f:
            f.write(response.content)
        os.rename(temp_path, target_path)
    except Exception:
        log_traceback(f"Unable to write CG item to {target_path}")
        return False
    if verbose:
        elapsed = time.monotonic() - start_time
        logging.info(f"CG {method} downloaded in {elapsed:.02f}s")
    return True

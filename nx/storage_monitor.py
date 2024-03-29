__all__ = ["StorageMonitor"]

import os
import time
import subprocess

from nxtools import logging

from nx.agents import BaseAgent
from nx.core.common import config, storages, Storage, ismount
from nx.db import DB


# id_storage: is_alive, check_interval, last_check
storage_status = {key: [True, 2, 0] for key in storages}


class StorageMonitor(BaseAgent):
    def main(self):
        storages_conf = config.get("storages", "all")

        db = DB()
        db.query("SELECT id, settings FROM storages")
        for id_storage, storage_settings in db.fetchall():
            if type(storages_conf) == list and id_storage not in storages_conf:
                continue

            storage = Storage(id_storage, **storage_settings)

            if storage:
                storage_string = f"{config['site_name']}:{storage.id}"
                storage_ident_path = os.path.join(storage.local_path, ".nebula_root")

                if not (
                    os.path.exists(storage_ident_path)
                    and storage_string
                    in [line.strip() for line in open(storage_ident_path).readlines()]
                ):
                    try:
                        with open(storage_ident_path, "a") as f:
                            f.write(storage_string + "\n")
                    except Exception:
                        if self.first_run:
                            logging.warning(f"{storage} is mounted, but read only")
                    else:
                        if self.first_run:
                            logging.info(f"{storage} is mounted and root is writable")
                continue

            s, i, lcheck = storage_status.get(id_storage, [True, 2, 0])

            if not s and time.time() - lcheck < i:
                continue

            if s:
                logging.info(f"{storage} is not mounted. Mounting...")
            if not os.path.exists(storage.local_path):
                try:
                    os.mkdir(storage.local_path)
                except Exception:
                    if s:
                        logging.error(f"Unable to create mountpoint for {storage}")
                    storage_status[id_storage] = [False, 240, time.time()]
                    continue

            self.mount(storage)

            if ismount(storage.local_path):
                logging.goodnews(f"{storage} mounted successfully")
                if id_storage not in storage_status:
                    storage_status[id_storage] = [True, 2, 0]
                storage_status[id_storage][0] = True
                storage_status[id_storage][1] = 2
            else:
                if s:
                    logging.error(f"{storage} mounting failed")
                storage_status[id_storage][0] = False
                check_interval = storage_status[id_storage][1]
                storage_status[id_storage][1] = min(240, check_interval * 2)

            storage_status[id_storage][2] = time.time()

    def mount(self, storage):
        if storage["protocol"] == "samba":
            smbopts = {}
            if storage.get("login"):
                smbopts["user"] = storage["login"]
            if storage.get("password"):
                smbopts["pass"] = storage["password"]
            if storage.get("domain"):
                smbopts["domain"] = storage["domain"]
            smbver = storage.get("samba_version", "3.0")
            if smbver:
                smbopts["vers"] = smbver

            if smbopts:
                opts = " -o '{}'".format(
                    ",".join(["{}={}".format(k, smbopts[k]) for k in smbopts])
                )
            else:
                opts = ""
            cmd = f"mount.cifs {storage['path']} {storage.local_path}{opts}"

        elif storage["protocol"] == "nfs":
            cmd = f"mount.nfs {storage['path']} {storage.local_path}"
        else:
            return

        proc = subprocess.Popen(cmd, shell=True)
        while proc.poll() is None:
            time.sleep(0.1)
        if proc.returncode:
            logging.error(f"Unable to mount {storage}")

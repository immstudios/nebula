import os
import time

from nxtools import s2time, logging, get_files, get_base_name, log_traceback

from nx.core.common import config, storages
from nx.core.enum import ObjectStatus, MediaType
from nx.db import DB
from nx.objects import Asset
from nx.base_service import BaseService
from nx.helpers import asset_by_path
from nx.filetypes import FileTypes


class Service(BaseService):
    def on_init(self):
        pass

    def on_main(self):
        db = DB()
        self.existing = []
        start_time = time.time()
        db.query("SELECT meta FROM assets WHERE media_type=1 AND status=1")
        for (meta,) in db.fetchall():
            asset = Asset(meta=meta, db=db)
            file_path = asset.file_path
            self.existing.append(file_path)
        duration = time.time() - start_time
        if duration > 5 or config.get("debug_mode", False):
            logging.debug(f"Online assets loaded in {s2time(duration)}")

        start_time = time.time()
        for wf_settings in self.settings.findall("folder"):
            id_storage = int(wf_settings.attrib["id_storage"])
            rel_wf_path = wf_settings.attrib["path"]
            quarantine_time = int(wf_settings.attrib.get("quarantine_time", "10"))
            id_folder = int(wf_settings.attrib.get("id_folder", 12))

            storage_path = storages[id_storage].local_path
            watchfolder_path = os.path.join(storage_path, rel_wf_path)

            if not os.path.exists(watchfolder_path):
                logging.warning("Skipping non-existing watchfolder", watchfolder_path)
                continue

            i = 0
            for file_object in get_files(
                watchfolder_path,
                recursive=wf_settings.attrib.get("recursive", False),
                hidden=wf_settings.attrib.get("hidden", False),
                case_sensitive_exts=wf_settings.get("case_sensitive_exts", False),
            ):
                i += 1
                if i % 100 == 0 and config.get("debug_mode", False):
                    logging.debug("{} files scanned".format(i))

                if not file_object.size:
                    continue

                full_path = file_object.path
                if full_path in self.existing:
                    continue

                now = time.time()
                asset_path = full_path.replace(storage_path, "", 1).lstrip("/")
                ext = os.path.splitext(asset_path)[1].lstrip(".").lower()
                if ext not in FileTypes.exts():
                    continue

                asset = asset_by_path(id_storage, asset_path, db=db)
                if asset:
                    self.existing.append(full_path)
                    continue

                base_name = get_base_name(asset_path)

                if quarantine_time and now - file_object.mtime < quarantine_time:
                    logging.debug(f"{base_name} is too young. Skipping")
                    continue

                asset = Asset(db=db)
                asset["content_type"] = FileTypes.by_ext(ext)
                asset["media_type"] = MediaType.FILE
                asset["id_storage"] = id_storage
                asset["path"] = asset_path
                asset["ctime"] = now
                asset["mtime"] = now
                asset["status"] = ObjectStatus.CREATING
                asset["id_folder"] = id_folder
                asset["title"] = base_name

                asset.load_sidecar_metadata()

                failed = False
                for post_script in wf_settings.findall("post"):
                    try:
                        exec(post_script.text)
                    except Exception:
                        log_traceback(f"Error executing post-script on {asset}")
                        failed = True

                if not failed:
                    asset.save(set_mtime=False)

        duration = time.time() - start_time
        if duration > 60 or config.get("debug_mode", False):
            logging.debug(f"Watchfolders scanned in {s2time(duration)}")

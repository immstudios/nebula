from nx import *
from nx.services import BaseService
from nx.objects import *

THUMBS = [
    [(32,18),   "xs"],
    [(160,90),  "s"],
    [(512,288), "m"],
    [(960,540), "l"]
    ]


def create_video_thumbnail(source, tbase, resolution=(512,288)):
    w, h = resolution
    target = tbase + "0.jpg"
    cmd = "ffmpeg -y -i \"{source}\" -vf \"thumbnail,scale={w}:{h}\" -frames:v 1 \"{target}\" ".format(source=source, target=target, w=w, h=h)
    proc = shell(cmd)
    if proc.retcode > 0:
        return False
    return True


class Service(BaseService):
    def on_init(self):
        try:
            self.thumb_root = os.path.join (
                storages[int(config.get("thumb_storage",0))].local_path,
                config["thumb_root"]
                )
        except KeyError:
            logging.error("Thumbnail root is not defined")
            self.thumb_root = False

    def on_main(self):
        if not self.thumb_root:
            return

        db = DB()
        db.query("SELECT meta FROM assets WHERE status=1 AND media_type=0 AND meta->>'has_thumbnail' NOT IN (1,2)")
        for meta, in db.fetchall():
            asset = Asset(meta=meta, db=db)
            spath = asset.file_path
            tpath = os.path.join(self.thumb_root, "{:04d}".format(int(asset.id/1000)), "{:d}".format(asset.id))

            if not os.path.exists(tpath):
                try:
                    os.makedirs(tpath)
                except:
                    logging.error("Unable to create thumbnail output directory {}".format(tpath))
                    continue

            for resolution, suffix in THUMBS:
                tbase = "{}{}".format(asset.id, suffix)
                if create_video_thumbnail(spath, os.path.join(tpath, tbase), resolution):
                    asset["has_thumbnail"] = 1
                else:
                    asset["has_thumbnail"] = 2
                asset.save()

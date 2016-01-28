from nx import *
from nx.objects import Asset
from nx.services import BaseService

class BaseAnalyzer():
    condition = False
    proc_name = "base"
    version   = 1.0

    def __init__(self, asset):
        self.asset = asset
        self.result = {}
        self.status = self.proc()

    def update(self, key, value):
        self.result[key] = value

    def proc(self):
        pass



class Analyzer_AV(BaseAnalyzer):
    condition = "asset['content_type'] in [AUDIO, VIDEO]"
    proc_name = "av"
    version   = 1.0

    def proc(self):
        fname = self.asset.file_path
        tags = [
                ("mean_volume:", "audio/gain/mean"),
                ("max_volume:",  "audio/gain/peak"),
                ("I:",           "audio/r128/i"),
                ("Threshold:",   "audio/r128/t"),
                ("LRA:",         "audio/r128/lra"),
                ("Threshold:",   "audio/r128/lra/t"),
                ("LRA low:",     "audio/r128/lra/l"),
                ("LRA high:",    "audio/r128/lra/r"),
            ]
        exp_tag = tags.pop(0)
        s = shell("ffmpeg -i \"{}\" -vn -filter_complex silencedetect=n=-20dB:d=5,ebur128,volumedetect -f null -".format(fname))
        silences = []
        for line in s.stderr().readlines():
            line = line.strip()

            if line.find("silence_end") > -1:
                e, d = line.split("|")
                e = e.split(":")[1].strip()
                d = d.split(":")[1].strip()

                try:
                    e = float(e)
                    s = max(0, e - float(d))
                except:
                    pass
                else:
                    silences.append([s, e])


            if line.find(exp_tag[0]) > -1:
                value = float(line.split()[-2])
                self.update(exp_tag[1], value)
                try:
                    exp_tag = tags.pop(0)
                except:
                    break

        if silences:
            self.update("qc/silence", silences)

        return True


class Analyzer_BPM(BaseAnalyzer):
    condition = "asset['id_folder'] == 5"
    proc_name = "bpm"
    version   = 1.0

    def proc(self):
        fname = self.asset.file_path
        s = shell("ffmpeg -i \"{}\" -vn -ar 44100 -f f32le - 2> /dev/null | bpm".format(fname))
        try:
            bpm = float(s.stdout().read())
        except:
            return False
        self.update("audio/bpm", bpm)
        return True




class Service(BaseService):
    def on_init(self):
      self.max_mtime = 0
      self.analyzers = [
        Analyzer_AV,
        Analyzer_BPM
        ]

    def on_main(self):
        db = DB()
        db.query("SELECT id_object, mtime FROM nx_assets WHERE status = '{}' and mtime > {} ORDER BY mtime DESC".format(ONLINE, self.max_mtime))
        res = db.fetchall()
        if res:
            logging.debug("{} assets will be analyzed".format(len(res)))

            for id_asset, mtime in res:
                self.max_mtime = max(self.max_mtime, mtime)
                self._proc(id_asset, db)

    def _proc(self, id_asset, db):
        asset = Asset(id_asset, db = db)
        for analyzer in self.analyzers:

            qinfo = asset["qc/analyses"] or {}
            if type(qinfo) in [str, unicode]:
                qinfo = json.loads(qinfo)

            if analyzer.proc_name in qinfo and (qinfo[analyzer.proc_name] == -1 or qinfo[analyzer.proc_name] >= analyzer.version ):
                continue

            if eval(analyzer.condition):
                logging.info("Analyzing {} using '{}'".format(asset, analyzer.proc_name))
                a = analyzer(asset)

                ## Reload asset (it may be changed by someone during analysis
                del(asset)
                asset = Asset(id_asset, db=db)
                result = -1 if not a.status else analyzer.version

                qinfo = asset["qc/analyses"] or {}
                if type(qinfo) == str:
                    qinfo = json.loads(qinfo)
                qinfo[analyzer.proc_name] = result
                asset["qc/analyses"] = qinfo

                ## Save result
                for key in a.result:
                    value = a.result[key]
                    if value:
                        logging.debug("Set {} {} to {}".format(asset, key, value))
                        asset[key] = value
                asset.save()
                self.heartbeat()

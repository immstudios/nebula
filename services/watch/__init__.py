from nx import *
from nx.services import BaseService
from nx.objects import *
from nx.core.filetypes import file_types


class Service(BaseService):
    def on_init(self):
        self.mirrors = self.settings.findall("mirror")
        self.ignore = []

    def on_main(self):
        db = DB()
        abp_cache = {}
        for mirror in self.mirrors:
            ###################
            ## Mirror settings

            mstorage = int(mirror.find("id_storage").text)
            mpath    = mirror.find("path").text
            stpath   = storages[mstorage].local_path

            try:    filters = mirror.find("filters").findall("filter")
            except: filters = []

            try:    mrecursive = int(mirror.find("recursive").text)
            except: mrecursive = 0

            try:    mhidden = int(mirror.find("hidden").text)
            except: mhidden = 0

            ## Mirror settings
            ###################
            now = time.time()

            for f in get_files(os.path.join(stpath,mpath), recursive=mrecursive, hidden=mhidden):

                apath = os.path.normpath(f.replace(stpath,""))
                apath = apath.lstrip("/")
                if apath == "": continue

                try:
                    filetype = file_types[os.path.splitext(f)[1][1:].lower()]
                except:
                    continue


                if filters:
                    for f in filters:
                        if CONTENT_TYPES.get(f.text.upper(), "blah blah") == filetype:
                          break
                    else:
                        continue


                if now - abp_cache.get("{}|{}".format(mstorage,apath),0) > 600:
                    if asset_by_path(mstorage,apath,db=db):
                        continue

                if (mstorage, apath) in self.ignore:
                    continue

                logging.debug("Found new file '{}'".format(apath))

                asset = Asset()
                asset["id_storage"]    = mstorage
                asset["path"]          = apath
                asset["title"]         = file_to_title(apath)
                asset["content_type"]  = filetype
                asset["media_type"]    = FILE
                asset["status"]        = CREATING

                asset.load_sidecar_metadata()

                for mt in mirror.findall("meta"):
                    try:
                        if mt.attrib["type"] == "script":
                            exec "asset[mt.attrib[\"tag\"]] = %s"% (mt.text or "")
                        else:
                            raise Exception
                    except:
                        asset[mt.attrib["tag"]] = mt.text or ""

                failed = False
                for post_script in mirror.findall("post"):
                    try:
                        exec(post_script.text)
                    except:
                        log_traceback("Error executing post-script on {}".format(asset))
                        failed = True

                if not failed:
                    asset.save()
                    logging.info("Created %s from %s"%(asset, apath))
                else:
                    logging.info("Post script failed. Ignoring file.")
                    self.ignore.append((mstorage, apath))
